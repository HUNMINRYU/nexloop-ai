from __future__ import annotations

from typing import Any

from services.pipeline.side_effects import SideEffectManager
from services.pipeline.stages.diversity_scorer import AuthorDiversityScorer
from services.pipeline.stages.filter import QualityFilter
from services.pipeline.stages.hydration import FeatureHydrator
from services.pipeline.stages.multi_diversity_scorer import MultiDiversityScorer
from services.pipeline.stages.scorer import EngagementScorer
from services.pipeline.stages.selector import TopInsightSelector
from services.pipeline.stages.source import CommentSource
from services.pipeline.types import Candidate
from utils.logger import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator:
    """
    X-Algorithm Pipeline Controller (Home Mixer)
    Source -> Hydration -> Filter -> Scorer -> Diversity -> Reranker -> Selector
    각 stage별 graceful degradation 지원
    """

    def __init__(
        self,
        source: CommentSource,
        hydrator: FeatureHydrator,
        quality_filter: QualityFilter,
        scorer: EngagementScorer,
        selector: TopInsightSelector,
        diversity_scorer: AuthorDiversityScorer | None = None,
        multi_diversity_scorer: MultiDiversityScorer | None = None,
        reranker: Any = None,
        side_effects: SideEffectManager | None = None,
        use_multi_diversity: bool = False,
    ):
        self.source = source
        self.hydrator = hydrator
        self.filter = quality_filter
        self.scorer = scorer
        self.selector = selector
        self.diversity_scorer = diversity_scorer
        self.multi_diversity_scorer = multi_diversity_scorer
        self.reranker = reranker
        self.side_effects = side_effects or SideEffectManager()
        self.use_multi_diversity = use_multi_diversity

    async def run_pipeline(self, raw_data: list[dict[str, Any]]) -> dict[str, Any]:
        stats: dict[str, Any] = {}

        # 1. Source: Raw Data -> Candidate 변환
        candidates = self.source.item_to_candidate(raw_data)
        original_count = len(candidates)
        stats["original_count"] = original_count

        # 2.1 Pre-Hydration Filter (명백한 스팸 제거로 LLM 비용 절감)
        candidates = self._safe_stage(
            "pre_filter", lambda c: self.filter.filter(c), candidates
        )
        stats["filtered_count"] = len(candidates)

        if not candidates:
            return {"insights": [], "stats": stats}

        # 2.2 Candidate Hydration (LLM)
        candidates = await self._safe_async_stage(
            "hydration", self.hydrator.hydrate, candidates
        )

        # 2.3 Post-Hydration Filter
        candidates = self._safe_stage(
            "post_filter", lambda c: self.filter.filter(c), candidates
        )
        stats["post_filtered_count"] = len(candidates)

        if not candidates:
            return {"insights": [], "stats": stats}

        # 3. Scorer: Weighting & Ranking
        ranked_candidates = self._safe_stage(
            "scoring", self.scorer.score, candidates
        )

        # 4. Diversity Scoring
        if self.use_multi_diversity and self.multi_diversity_scorer:
            ranked_candidates = self._safe_stage(
                "multi_diversity",
                self.multi_diversity_scorer.apply,
                ranked_candidates,
            )
        elif self.diversity_scorer:
            ranked_candidates = self._safe_stage(
                "diversity", self.diversity_scorer.apply, ranked_candidates
            )

        # 5. Reranking (있을 경우)
        if self.reranker is not None:
            ranked_candidates = await self._safe_async_stage(
                "reranking", self.reranker.rerank, ranked_candidates
            )

        stats["processed_count"] = len(ranked_candidates)

        # 6. Selection: Top K 선정 및 포맷팅
        final_result = self.selector.select(ranked_candidates, top_k=5)

        # Side effects: 파이프라인 완료 이벤트
        self.side_effects.emit(
            "pipeline_completed",
            stats=stats,
            result_count=len(final_result),
        )

        return {"insights": final_result, "stats": stats}

    def _safe_stage(
        self,
        stage_name: str,
        fn: Any,
        candidates: list[Candidate],
    ) -> list[Candidate]:
        """동기 stage를 안전하게 실행 (실패 시 backup 사용)"""
        backup = list(candidates)
        try:
            return fn(candidates)
        except Exception as e:
            logger.error(f"{stage_name} 실패, backup 사용: {e}")
            self.side_effects.emit(
                "stage_error", stage=stage_name, error=str(e)
            )
            return backup

    async def _safe_async_stage(
        self,
        stage_name: str,
        fn: Any,
        candidates: list[Candidate],
    ) -> list[Candidate]:
        """비동기 stage를 안전하게 실행 (실패 시 backup 사용)"""
        backup = list(candidates)
        try:
            return await fn(candidates)
        except Exception as e:
            logger.error(f"{stage_name} 실패, backup 사용: {e}")
            self.side_effects.emit(
                "stage_error", stage=stage_name, error=str(e)
            )
            return backup
