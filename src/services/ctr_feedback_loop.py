"""CTR Feedback Loop - 예측 vs 실제 성과 비교로 지속 학습"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class CTRFeedbackLoop:
    """
    CTR 예측/실제 기록 및 오차 분석.
    가중치 자동 튜닝을 위한 데이터 수집.
    """

    def __init__(self, db_session: Any = None):
        self._db = db_session
        # In-memory 저장소 (DB 없을 때)
        self._records: List[Dict[str, Any]] = []

    async def record_prediction(
        self,
        video_id: str,
        predicted_ctr: float,
        model_version: str = "v1",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """예측 CTR 기록"""
        record = {
            "video_id": video_id,
            "predicted_ctr": predicted_ctr,
            "model_version": model_version,
            "metadata": metadata,
        }

        if self._db is not None:
            try:
                await self._save_prediction_to_db(record)
            except Exception as e:
                logger.warning(f"CTR 예측 DB 저장 실패: {e}")
                self._records.append(record)
        else:
            self._records.append(record)

    async def record_actual(
        self, video_id: str, actual_ctr: float
    ) -> Optional[Dict[str, Any]]:
        """실제 CTR 기록 및 오차 계산"""
        if self._db is not None:
            try:
                return await self._update_actual_in_db(video_id, actual_ctr)
            except Exception as e:
                logger.warning(f"CTR 실제 DB 업데이트 실패: {e}")

        # In-memory fallback
        for record in reversed(self._records):
            if record["video_id"] == video_id and "actual_ctr" not in record:
                record["actual_ctr"] = actual_ctr
                record["error"] = actual_ctr - record["predicted_ctr"]
                return record
        return None

    def compute_adjustment_weights(
        self, records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, float]:
        """오차 분석 기반 가중치 조정 추천"""
        data = records or [
            r for r in self._records if "actual_ctr" in r and "error" in r
        ]
        if not data:
            return {}

        errors = [r["error"] for r in data]
        avg_error = sum(errors) / len(errors)
        abs_errors = [abs(e) for e in errors]
        mae = sum(abs_errors) / len(abs_errors)

        return {
            "avg_error": round(avg_error, 4),
            "mae": round(mae, 4),
            "bias_direction": "over" if avg_error > 0 else "under",
            "sample_count": len(data),
            "suggested_correction": round(-avg_error * 0.5, 4),
        }

    async def _save_prediction_to_db(self, record: Dict[str, Any]) -> None:
        from infrastructure.database.models import CTRFeedback

        row = CTRFeedback(
            video_id=record["video_id"],
            predicted_ctr=str(record["predicted_ctr"]),
            model_version=record["model_version"],
            metadata_json=json.dumps(record.get("metadata") or {}),
        )
        self._db.add(row)
        await self._db.commit()

    async def _update_actual_in_db(
        self, video_id: str, actual_ctr: float
    ) -> Optional[Dict[str, Any]]:
        from sqlalchemy import select, desc
        from infrastructure.database.models import CTRFeedback

        stmt = (
            select(CTRFeedback)
            .where(CTRFeedback.video_id == video_id)
            .where(CTRFeedback.actual_ctr.is_(None))
            .order_by(desc(CTRFeedback.created_at))
            .limit(1)
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            return None

        predicted = float(row.predicted_ctr)
        error = actual_ctr - predicted
        row.actual_ctr = str(actual_ctr)
        row.error = str(round(error, 4))
        await self._db.commit()

        return {
            "video_id": video_id,
            "predicted_ctr": predicted,
            "actual_ctr": actual_ctr,
            "error": error,
        }
