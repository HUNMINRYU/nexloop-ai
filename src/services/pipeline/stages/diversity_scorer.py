from typing import Dict, List

from services.pipeline.types import Candidate


class AuthorDiversityScorer:
    """
    동일 작성자 반복 등장 시 점수 감쇠로 피드 다양성 확보
    Floor 보호값으로 완전 억제 방지 (x-algorithm 방식)
    """

    def __init__(self, decay_factor: float = 0.7, floor: float = 0.3):
        self.decay_factor = decay_factor
        self.floor = floor

    def _calculate_multiplier(self, position: int) -> float:
        """position번째 등장에 대한 감쇠 배율 (floor 이하로 내려가지 않음)"""
        return (1.0 - self.floor) * (self.decay_factor ** position) + self.floor

    def apply(self, candidates: List[Candidate]) -> List[Candidate]:
        author_counts: Dict[str, int] = {}

        for candidate in candidates:
            author = candidate.author.username
            count = author_counts.get(author, 0)

            if count > 0:
                multiplier = self._calculate_multiplier(count)
                candidate.score.final_score *= multiplier
                candidate.score.weighted_components["diversity_decay"] = round(
                    multiplier, 3
                )

            author_counts[author] = count + 1

        return sorted(candidates, key=lambda c: c.score.final_score, reverse=True)
