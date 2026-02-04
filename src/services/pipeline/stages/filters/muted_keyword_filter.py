import re

from services.pipeline.types import Candidate


class MutedKeywordFilter:
    """특정 키워드 포함 콘텐츠 제거 (word boundary 기반 정확 매칭)"""

    DEFAULT_MUTED: set[str] = {"광고", "홍보", "스팸", "카톡", "텔레그램", "링크"}

    def __init__(self, keywords: set[str] | None = None):
        self.keywords = keywords or self.DEFAULT_MUTED
        # 각 키워드에 대해 word boundary 패턴 컴파일
        # 한국어는 \b가 제대로 동작하지 않을 수 있으므로
        # 앞뒤가 같은 문자 종류가 아닌지 확인하는 패턴 사용
        self._patterns = [
            re.compile(
                rf'(?<!\w){re.escape(kw)}(?!\w)',
                re.IGNORECASE,
            )
            for kw in self.keywords
        ]

    def filter(self, candidates: list[Candidate]) -> list[Candidate]:
        return [c for c in candidates if not self._contains_muted(c)]

    def _contains_muted(self, candidate: Candidate) -> bool:
        text = candidate.content
        return any(pattern.search(text) for pattern in self._patterns)
