from typing import List, Iterable

from services.pipeline.types import Candidate
from utils.bloom_filter import BloomFilter


class PreviouslySeenFilter:
    """이미 본 콘텐츠 제거 (set 또는 bloom filter 기반)"""

    def __init__(
        self,
        seen_ids: Iterable[str] | None = None,
        use_bloom: bool = False,
        bloom_expected_items: int = 10000,
        bloom_fp_rate: float = 0.01,
    ):
        self.use_bloom = use_bloom
        ids = [i for i in (seen_ids or []) if i]

        if use_bloom and ids:
            self._bloom = BloomFilter(
                expected_items=max(len(ids), bloom_expected_items),
                fp_rate=bloom_fp_rate,
            )
            self._bloom.bulk_add(ids)
            self._set = None
        else:
            self._set = set(ids)
            self._bloom = None

    def filter(self, candidates: List[Candidate]) -> List[Candidate]:
        if self._bloom is not None:
            return [c for c in candidates if not self._bloom.contains(c.id)]
        if not self._set:
            return candidates
        return [c for c in candidates if c.id not in self._set]
