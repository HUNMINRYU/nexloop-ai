import math
from typing import List

from services.pipeline.types import Candidate, CandidateScore


class EngagementScorer:
    """
    X-Algorithm의 Weighted Scoring 로직 구현
    Formula: Final Score = Σ (weight_i × P(action_i)) + offset
    positive/negative 점수를 분리 후 offsetting 적용
    """

    # 가중치 설정 (19개 signal)
    WEIGHTS = {
        # 긍정적 시그널
        "purchase_intent": 10.0,
        "constructive_feedback": 5.0,
        "reply_inducing": 3.0,
        "share_probability": 8.0,
        "viral_potential": 7.0,
        "actionable_insight": 6.0,
        "quote_worthy": 4.0,
        "save_worthy": 5.0,
        "follow_author": 4.0,
        "dwell_time": 2.0,
        # 확장 시그널 (x-algorithm)
        "dm_probability": 3.0,
        "copy_link_probability": 4.0,
        "profile_click": 3.0,
        "bookmark_worthy": 5.0,
        # 부정적 시그널
        "toxicity": -100.0,
        "controversy_score": -2.0,
        "not_interested": -5.0,
        "report_probability": -50.0,
    }

    # Negative가 positive를 과도하게 압도하지 않도록 보정하는 offset 비율
    NEGATIVE_OFFSET_RATIO = 0.5

    def score(self, candidates: List[Candidate]) -> List[Candidate]:
        for candidate in candidates:
            self._calculate_single_candidate(candidate)

        # 점수 내림차순 정렬 (Ranking)
        return sorted(candidates, key=lambda c: c.score.final_score, reverse=True)

    def _calculate_single_candidate(self, candidate: Candidate) -> None:
        features = candidate.features
        score_components = {}
        positive_score = 0.0
        negative_score = 0.0
        reasons = []

        # 1. Feature 기반 가중치 합산 (19개 signal)
        feature_dict = {
            "purchase_intent": features.purchase_intent,
            "constructive_feedback": features.constructive_feedback,
            "reply_inducing": features.reply_inducing,
            "share_probability": features.share_probability,
            "viral_potential": features.viral_potential,
            "actionable_insight": features.actionable_insight,
            "quote_worthy": features.quote_worthy,
            "save_worthy": features.save_worthy,
            "follow_author": features.follow_author,
            "dwell_time": features.dwell_time,
            "dm_probability": features.dm_probability,
            "copy_link_probability": features.copy_link_probability,
            "profile_click": features.profile_click,
            "bookmark_worthy": features.bookmark_worthy,
            "toxicity": features.toxicity,
            "controversy_score": features.controversy_score,
            "not_interested": features.not_interested,
            "report_probability": features.report_probability,
        }

        for feature_name, probability in feature_dict.items():
            weight = self.WEIGHTS.get(feature_name, 0.0)
            if weight == 0 or probability == 0:
                continue

            component_score = weight * probability
            score_components[feature_name] = component_score

            if component_score >= 0:
                positive_score += component_score
            else:
                negative_score += abs(component_score)

            # 설명 생성용 (Top factor만)
            if abs(component_score) > 2.0:
                effect = "높여" if component_score > 0 else "낮춰"
                reasons.append(f"{feature_name}({probability:.1f})가 점수를 {effect}줌")

        # 2. Score Offsetting: negative가 positive를 과도하게 압도하지 않도록 보정
        # negative_score가 positive_score보다 클 경우, 초과분에 offset 비율 적용
        if negative_score > positive_score:
            excess = negative_score - positive_score
            adjusted_negative = positive_score + excess * self.NEGATIVE_OFFSET_RATIO
        else:
            adjusted_negative = negative_score

        raw_score = positive_score - adjusted_negative

        # 3. Engagement boost (Log Scale - x-algorithm 스타일)
        engagement_boost = min(math.log1p(candidate.like_count) * 1.5, 5.0)
        if engagement_boost > 0:
            raw_score += engagement_boost
            score_components["engagement_boost"] = round(engagement_boost, 2)

        candidate.score = CandidateScore(
            final_score=round(raw_score, 2),
            raw_score=round(positive_score - negative_score, 2),
            positive_score=round(positive_score, 2),
            negative_score=round(negative_score, 2),
            weighted_components=score_components,
            explanation=", ".join(reasons) if reasons else "일반적인 댓글",
        )
