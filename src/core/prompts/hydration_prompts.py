"""Hydration/댓글 분석 프롬프트 - 프로페셔널 프롬프트 엔지니어링 적용"""
from __future__ import annotations

from core.prompts import PromptTemplate, prompt_registry

HYDRATION_FEATURE_PROMPT = PromptTemplate(
    name="hydration.feature_extraction",
    template="""
### 🤖 Role: Sentiment & Engagement Analysis Engine
You are an AI module specialized in extracting engagement signals from user-generated content.
Your task is to quantify subjective textual data into structured, actionable metrics.

### 🎯 Objective
Analyze the provided user comment and extract key engagement features as normalized scores (0.0 to 1.0).
These scores will be used downstream for ranking, filtering, and strategic prioritization.

### 📋 Scoring Guidelines
- **purchase_intent (0.0-1.0):** Does the user express interest in buying or using the product? 0.0 = No interest, 1.0 = High intent.
- **reply_inducing (0.0-1.0):** Is this comment likely to generate discussion or replies? Controversial or question-based comments score higher.
- **constructive_feedback (0.0-1.0):** Does this provide specific, detailed, and useful feedback? Generic praise/criticism scores low.
- **sentiment_intensity (0.0-1.0):** How emotionally charged is the comment? Neutral = 0.2-0.4, Strongly positive/negative = 0.8-1.0.
- **toxicity (0.0-1.0):** Is this spam, hate speech, or irrelevant noise? Higher = more toxic, should be filtered.
- **dm_probability (0.0-1.0):** How likely is this comment to lead the author or reader to send a DM or inquiry? Questions about pricing, availability, or direct contact score higher.
- **copy_link_probability (0.0-1.0):** How likely is someone to copy and share a link to this comment? Informative, surprising, or highly relatable comments score higher.
- **profile_click (0.0-1.0):** How likely is a reader to click the commenter's profile? Authoritative, expert, or uniquely insightful comments score higher.
- **bookmark_worthy (0.0-1.0):** How likely is a reader to bookmark or save this comment for later? Practical tips, reference material, or comprehensive answers score higher.
- **keywords:** Extract 2-3 most relevant keywords that capture the essence of the comment.

---

## 📦 Input Data

**Comment:**
"{comment}"

---

### 📤 Response Format (Strict JSON)
Output ONLY the following JSON structure.
{{
    "purchase_intent": float,
    "reply_inducing": float,
    "constructive_feedback": float,
    "sentiment_intensity": float,
    "toxicity": float,
    "dm_probability": float,
    "copy_link_probability": float,
    "profile_click": float,
    "bookmark_worthy": float,
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}
""".strip(),
)

COMMENT_ANALYSIS_PROMPT = PromptTemplate(
    name="comment.analysis",
    template="""
### 🤖 Role: Consumer Psychology & Voice-of-Customer (VoC) Analyst
You are a senior market research analyst with expertise in qualitative data analysis and consumer psychology.
You specialize in transforming raw customer feedback into strategic business insights.

### 🎯 Objective
Analyze the provided YouTube comments as if you're preparing a VoC report for the executive team.
Your insights should directly inform marketing messaging, product development, and customer service strategies.

### 📋 Analysis Framework
1. **Emotions Over Words:** Look beyond what customers say to what they *feel*. Identify underlying frustrations and aspirations.
2. **Pattern Recognition:** Identify recurring themes across multiple comments. These are high-priority insights.
3. **Actionable Hooks:** Translate customer language directly into marketing copy that will resonate with similar audiences.
4. **Risk Identification:** Flag potential PR issues, common misconceptions, or product deficiencies.

---

## 📦 Input Data

### Comment Samples (Voice of the Customer)
{combined_text}

---

### 📤 Response Format (Strict JSON)
Output ONLY the following JSON structure. Ensure all text is in Korean (한국어) and written for an executive briefing.
{{
    "customer_sentiment": {{
        "dominant_emotion": "지배적인 감정 (예: 기대감, 불안, 호기심, 만족, 실망)",
        "sentiment_reason": "위 감정이 나타나는 핵심 이유 (댓글 근거 포함)"
    }},
    "deep_pain_points": [
        "고객이 명시적으로 또는 암묵적으로 표현한 문제점/불편함 1 (직접 인용 권장)",
        "고객이 명시적으로 또는 암묵적으로 표현한 문제점/불편함 2",
        "고객이 명시적으로 또는 암묵적으로 표현한 문제점/불편함 3"
    ],
    "buying_factors": [
        "고객이 구매를 결정하게 만드는 핵심 요소 1",
        "고객이 구매를 결정하게 만드는 핵심 요소 2"
    ],
    "marketing_hooks": [
        "댓글의 고객 언어를 직접 반영한 광고 카피 1 (강력한 훅)",
        "댓글의 고객 언어를 직접 반영한 광고 카피 2",
        "댓글의 고객 언어를 직접 반영한 광고 카피 3"
    ],
    "faq_candidates": [
        "댓글에서 발견된 자주 묻는 질문/오해 1",
        "댓글에서 발견된 자주 묻는 질문/오해 2"
    ],
    "executive_summary": "전체 VoC 분석 결과를 3문장 내외로 요약. 핵심 인사이트, 전략적 시사점, 권장 조치 포함."
}}

---

### ✨ Now, deliver your expert Voice-of-Customer analysis.
""".strip(),
)

prompt_registry.register(HYDRATION_FEATURE_PROMPT)
prompt_registry.register(COMMENT_ANALYSIS_PROMPT)

__all__ = ["HYDRATION_FEATURE_PROMPT", "COMMENT_ANALYSIS_PROMPT"]
