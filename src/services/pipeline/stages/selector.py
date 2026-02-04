from typing import Any

from services.pipeline.types import Candidate

# -------------------------------------------------------------------------


class TopInsightSelector:
    """최종 결과 선정 및 포맷팅 (Selection Layer)"""

    def select(
        self, ranked_candidates: list[Candidate], top_k: int = 3
    ) -> list[dict[str, Any]]:
        # 상위 K개 선정
        selected = ranked_candidates[:top_k]

        results = []
        for rank, cand in enumerate(selected, 1):
            cand.is_selected = True
            cand.selection_reason = f"Rank {rank}: {cand.score.explanation}"

            # UI에서 쓰기 편한 Dict 형태로 변환
            results.append(
                {
                    "rank": rank,
                    "author": cand.author.username,
                    "content": cand.content,
                    "score": cand.score.final_score,
                    "reason": cand.score.explanation,
                    "features": {
                        "purchase": cand.features.purchase_intent,
                        "viral": cand.features.reply_inducing,
                    },
                }
            )
        return results
