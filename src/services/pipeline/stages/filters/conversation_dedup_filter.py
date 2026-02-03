"""같은 대화 쓰레드의 댓글 중 최고 점수만 선택"""

from collections import defaultdict
from typing import List

from services.pipeline.types import Candidate


class ConversationDedupFilter:
    """
    동일 conversation_id를 가진 댓글 그룹에서 최고 점수 candidate만 유지.
    conversation_id가 없는 댓글은 그대로 통과.
    """

    def filter(self, candidates: List[Candidate]) -> List[Candidate]:
        if not candidates:
            return []

        groups: dict[str, list[Candidate]] = defaultdict(list)
        no_conversation: list[Candidate] = []

        for c in candidates:
            if c.conversation_id:
                groups[c.conversation_id].append(c)
            else:
                no_conversation.append(c)

        # 각 그룹에서 최고 점수 candidate 선택
        best_per_group: list[Candidate] = []
        for conv_id, group in groups.items():
            best = max(group, key=lambda c: c.score.final_score)
            best_per_group.append(best)

        return no_conversation + best_per_group
