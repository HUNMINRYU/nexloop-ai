from datetime import datetime
from typing import Any

from utils.logger import (
    get_logger,
    log_llm_fail,
    log_llm_request,
    log_llm_response,
    log_step,
    log_success,
)

logger = get_logger(__name__)

# === 훅 전략 프리셋 (9종, UI 표기용 label + LLM 프롬프트용 instruction) ===
HOOK_STRATEGIES = [
    {
        "key": "curiosity",
        "label": "Curiosity (호기심)",
        "instruction": "Write a clickbait hook that teases a secret or hidden truth without revealing it immediately. Make the user curious.",
    },
    {
        "key": "loss_aversion",
        "label": "Loss Aversion (손실 회피)",
        "instruction": "Emphasize the negative consequences or money/health lost by NOT using the product. Focus on pain points.",
    },
    {
        "key": "social_proof",
        "label": "Social Proof (사회적 증명)",
        "instruction": "Highlight popularity, user reviews, or 'everyone is doing it' mentality. Use numbers or rankings.",
    },
    {
        "key": "authority",
        "label": "Authority (권위)",
        "instruction": "Use a tone of expert recommendation, scientific backing, or official certification to build trust.",
    },
    {
        "key": "scarcity",
        "label": "Scarcity (희소성)",
        "instruction": "Emphasize limited quantity, limited stock, or exclusive access to make the product feel rare.",
    },
    {
        "key": "zeigarnik",
        "label": "Zeigarnik (미완성 효과)",
        "instruction": "Start a sentence but leave the conclusion open-ended (ellipsis...), forcing the user to click to finish the thought.",
    },
    {
        "key": "urgency",
        "label": "Urgency (긴급성)",
        "instruction": "Create a sense of immediate time pressure. Use words like 'Now', 'Today only', 'Ends soon'.",
    },
    {
        "key": "negativity",
        "label": "Negativity (공포/충격)",
        "instruction": "Shock the viewer with a scary fact or worst-case scenario related to the pest problem. High emotional impact.",
    },
    {
        "key": "benefit",
        "label": "Benefit (즉각적 혜택)",
        "instruction": "Focus purely on the positive, instant result. No fluff, just the dream outcome realized immediately.",
    },
    {
        "key": "trend",
        "label": "Trend / Meme (최신 유행)",
        "instruction": "Use current viral memes (e.g., Kim Dong-hyun, Han River Cat) or trending slang to make the product feel extremely relevant and hip.",
    },
]

# === 후킹 스타일 템플릿 (LLM 폴백·비디오 등에서 사용) ===
HOOK_STYLES = {
    "curiosity": {
        "name": "호기심형",
        "emoji": "🤔",
        "templates": [
            "99%가 모르는 {product}의 비밀",
            "{product} 이렇게 쓰면 효과 2배",
            "전문가들만 아는 {product} 활용법",
            "{benefit} 하려면 이것만 기억하세요",
        ],
        "description": "시청자의 호기심을 자극하여 끝까지 시청하게 만듦",
    },
    "fear": {
        "name": "공포형",
        "emoji": "😱",
        "templates": [
            "이거 안 쓰면 {pain_point} 계속됩니다",
            "{pain_point} 방치하면 이렇게 됩니다",
            "아직도 {wrong_method} 하세요? 큰일납니다",
            "{product} 없이 버티다간...",
        ],
        "description": "문제를 방치했을 때의 결과를 보여줌",
    },
    "reversal": {
        "name": "반전형",
        "emoji": "😮",
        "templates": [
            "처음엔 의심했는데... {benefit}",
            "솔직히 안 믿었어요, 근데 {result}",
            "이게 된다고? {product} 써보니까...",
            "거짓말인 줄 알았는데 {benefit} 실화",
        ],
        "description": "의심에서 확신으로의 전환 스토리",
    },
    "question": {
        "name": "질문형",
        "emoji": "❓",
        "templates": [
            "{pain_point} 고민이시죠?",
            "혹시 {pain_point} 때문에 고민 중이세요?",
            "{wrong_method} 하고 계신가요?",
            "{benefit} 원하시나요?",
        ],
        "description": "시청자의 고민에 공감하며 시작",
    },
    "urgency": {
        "name": "긴급형",
        "emoji": "⚡",
        "templates": [
            "지금 안 보면 후회합니다",
            "오늘만 공개되는 {product} 비법",
            "이 영상 내리기 전에 꼭 보세요",
            "{benefit} 원하면 지금 당장!",
        ],
        "description": "긴급함을 강조하여 즉시 행동 유도",
    },
    # === 심리 모델 (Marketing Psychology) ===
    "loss_aversion": {
        "name": "손실 회피형",
        "emoji": "📉",
        "templates": [
            "이 기회 놓치면 {loss} 손해봅니다",
            "오늘 지나면 혜택이 사라져요",
            "남들 다 {benefit} 받는데 혼자만...",
            "지금 안 쓰면 나중에 후회합니다",
        ],
        "description": "얻는 기쁨보다 잃는 고통이 2배 더 크다는 심리 활용",
    },
    "social_proof": {
        "name": "사회적 증거형",
        "emoji": "👥",
        "templates": [
            "이미 10만 명이 선택한 {product}",
            "왜 다들 {product} 이야기만 할까요?",
            "인기 폭발! {product} 써본 사람들 반응",
            "요즘 핫한 {product}, 이유가 있네요",
        ],
        "description": "남들도 다 쓴다! 대세감을 조성하여 안심시킴",
    },
    "authority": {
        "name": "권위 활용형",
        "emoji": "👨‍⚕️",
        "templates": [
            "전문가가 추천하는 {product} 사용법",
            "업계 1위가 {product} 선택한 이유",
            "의사/전문가들도 인정한 {benefit} 비결",
            "연구 결과로 증명된 {product} 효과",
        ],
        "description": "권위자의 추천이나 데이터를 통해 신뢰도 확보",
    },
    "scarcity": {
        "name": "희소성 강조형",
        "emoji": "⏳",
        "templates": [
            "딱 100개만 남았습니다",
            "지금 아니면 구할 수 없는 {product}",
            "재입고 문의 폭주! 품절 임박",
            "이번 달만 가능한 {benefit} 혜택",
        ],
        "description": "부족함을 강조하여 소유욕과 긴박감 자극",
    },
    "zeigarnik": {
        "name": "미완성 효과형",
        "emoji": "🧩",
        "templates": [
            "{product}의 숨겨진 기능 하나만 알면...",
            "이것만 알았어도 {pain_point} 없었을 텐데",
            "딱 하나만 바꿨는데 {benefit} 대박남",
            "99%가 놓치고 있는 {product} 사용 꿀팁",
        ],
        "description": "문장을 미완성처럼 느끼게 하여 궁금증 극대화",
    },
    "negativity": {
        "name": "공포/충격형",
        "emoji": "😱",
        "templates": [
            "자면서 바퀴벌레 먹을 확률 70%",
            "이거 안 쓰면 {pain_point} 계속됩니다",
            "{pain_point} 방치하면 이렇게 됩니다",
            "{product} 없이 버티다간...",
        ],
        "description": "부정적 상황(공포, 혐오)을 보여주어 해결책을 찾게 함",
    },
    "benefit": {
        "name": "즉각적 혜택형",
        "emoji": "✨",
        "templates": [
            "뿌리자마자 1초 만에 전멸",
            "{product} 하나로 {benefit}",
            "복잡한 과정 없이 {benefit}",
            "바로 느껴지는 {benefit}",
        ],
        "description": "복잡한 과정 없이 바로 얻을 수 있는 보상 강조",
    },
    "trend": {
        "name": "최신 밈/트렌드형",
        "emoji": "🔥",
        "templates": [
            "요즘 난리난 {product} 실체 ㄷㄷ",
            "이거 모르면 손해인 {product} 사용법",
            "인스타에서 품절 대란난 그 제품",
            "지금 제일 핫한 {benefit} 아이템",
        ],
        "description": "현재 가장 핫한 밈과 트렌드를 반영하여 화제성 확보",
    },
}


class HookService:
    """AI 기반 후킹 문구 생성 서비스"""

    def __init__(self, gemini_client=None) -> None:
        """
        Args:
            gemini_client: AI 기반 맞춤 후킹 생성 시 사용 (선택)
        """
        self._gemini = gemini_client

    def get_available_styles(self) -> list[dict]:
        """사용 가능한 후킹 스타일 목록 반환 (9종, UI 표기용 label)"""
        result = []
        for s in HOOK_STRATEGIES:
            key = s["key"]
            style = HOOK_STYLES.get(key, {})
            result.append(
                {
                    "key": key,
                    "name": s["label"],
                    "emoji": style.get("emoji", ""),
                    "description": style.get("description", ""),
                }
            )
        return result

    def generate_hooks(
        self,
        style: str,
        product: dict,
        pain_points: list[str] | None = None,
        count: int = 3,
        length: str = "long",  # short, medium, long
    ) -> list[str]:
        """
        특정 스타일의 후킹 문구 생성.
        LLM에 제품·제품설명을 전달해 생성 요청하고, 실패 시 템플릿 폴백.
        """
        p_name = product.get("name", "제품")
        p_desc = (product.get("description") or "").strip()
        p_target = (product.get("target") or "").strip()
        strategy = next((s for s in HOOK_STRATEGIES if s["key"] == style), None)
        style_normalized = style if style in HOOK_STYLES else "curiosity"
        style_name = HOOK_STYLES[style_normalized]["name"]
        instruction = strategy["instruction"] if strategy else None

        # 길이 옵션에 따른 글자 수 제한 설정
        length_guide = "20-30 Korean characters"
        if length == "short":
            length_guide = "UNDER 20 Korean characters (Short & Punchy)"
        elif length == "long":
            length_guide = "30-45 Korean characters (Descriptive & Story)"

        if self._gemini and hasattr(self._gemini, "generate_text"):
            log_llm_request(
                "훅 생성",
                f"LLM에게 제품·제품설명 전달, 스타일: {style_name}({style}), {count}개 요청 (제품: {p_name}, 길이: {length})",
            )
            strategy_instruction = (
                f"\n[Copywriting Strategy (CRITICAL - Follow Exactly)]\n{instruction}\n"
                if instruction
                else ""
            )
            prompt = f"""### 🤖 Role: Short-form Advertising Hook Specialist
            You are an elite Korean advertising copywriter specializing in scroll-stopping hook phrases for vertical short-form video platforms (Shorts, Reels, TikTok).
            You have mastered the psychological triggers that make viewers stop scrolling: Curiosity Gap, Loss Aversion, Social Proof, Urgency, and Emotional Resonance.
            
            ### 🎯 Objective
            Generate exactly {count} Korean hook phrases for the "{style_name}" style that:
            - Stop the scroll within 0.5 seconds
            - Create irresistible curiosity or emotional urgency
            - Drive immediate click-through
            {strategy_instruction}
            ### 📦 Product Context
            - **Product Name:** {p_name}
            - **Product Description:** {p_desc or "(정보 없음)"}
            - **Target Audience:** {p_target or "(정보 없음)"}
            
            ### 📋 Hook Writing Principles (CRITICAL)
            1. **Character Limit:** {length_guide}
            2. **Immediate Impact:** The reader must feel emotion in the first 3 characters
3. **No Generic Phrases:** Avoid clichés like "지금 바로" or "놓치지 마세요" unless strategically used
4. **Specificity Wins:** Numbers and concrete details outperform vague promises
5. **Colloquial Tone:** Write like a friend texting, not a corporate ad

### ✨ Few-Shot Examples (Quality Reference)
**Style: 호기심형** → "99%가 모르는 비밀" / "이거 알면 인생 바뀜" / "전문가도 깜짝 놀란"
**Style: 공포/충격형** → "자면서 먹을 수도" / "방치하면 이렇게 됨" / "이미 늦었을지도"
**Style: 긴급형** → "오늘 끝" / "품절 임박" / "마지막 기회"
**Style: 사회적 증거형** → "10만 명이 선택" / "후기 폭발" / "입소문 난 이유"

### 📤 Output Format (STRICT)
- Output ONLY the hook phrases, one per line
- NO numbers, bullets, dashes, or prefixes
- NO markdown, code blocks, or explanations
- Plain Korean text ONLY

### ✨ Now generate {count} high-converting hooks for {p_name}.
"""
            try:
                response = self._gemini.generate_text(prompt, temperature=0.6)
                lines = [
                    line.strip()
                    for line in (response or "").strip().split("\n")
                    if line.strip()
                ]
                # 번호/불릿 제거
                max_len = 60
                if length == "short":
                    max_len = 25
                elif length == "medium":
                    max_len = 40

                hooks = []
                for line in lines[: count + 5]:
                    clean = line.lstrip("0123456789.-) ").strip()
                    if clean and len(clean) <= max_len:
                        hooks.append(clean)
                        if len(hooks) >= count:
                            break
                if hooks:
                    log_llm_response(
                        "훅 생성", f"LLM이 제품·설명 반영해 {len(hooks)}개 생성 완료"
                    )
                    return hooks[:count]
            except Exception as e:
                log_llm_fail("훅 생성", str(e))
                logger.warning(f"LLM 훅 생성 실패, 템플릿 폴백: {e}")

        # 2) 폴백: 템플릿 기반 생성
        log_step("후킹 생성", style, f"제품: {p_name} (템플릿 폴백)")
        style_data = HOOK_STYLES[style_normalized]
        templates = style_data["templates"]
        p_benefit = product.get("benefit") or p_desc or p_target or "효과를 경험"
        if len(p_benefit) > 20:
            p_benefit = p_benefit[:18].rsplit(" ", 1)[0] or p_benefit[:18]
        pain_point = "고민"
        if pain_points and len(pain_points) > 0:
            pain_point = pain_points[0]
        elif product.get("pain_points"):
            pain_point = product["pain_points"][0]
        elif p_target:
            pain_point = (
                p_target
                if len(p_target) <= 8
                else p_target.replace("모든 ", "").split("/")[0].strip()
            )
        format_kwargs = {
            "product": p_name,
            "benefit": p_benefit,
            "pain_point": pain_point,
            "wrong_method": "기존 방법",
            "result": "진짜 효과가 있더라",
            "loss": "큰",
            "count": "10만",
            "discount": "30",
        }
        hooks = [
            templates[i].format(**format_kwargs)
            for i in range(min(count, len(templates)))
        ]
        log_success(f"{len(hooks)}개 후킹 문구 생성 완료 (템플릿)")
        return hooks

    # === Marketing Psychology Methods (Skill 적용) ===

    def generate_loss_aversion_hooks(self, product: dict, count: int = 3) -> list[str]:
        """손실 회피(Loss Aversion) 모델 적용 훅 생성"""
        return self.generate_hooks("loss_aversion", product, count=count)

    def generate_social_proof_hooks(self, product: dict, count: int = 3) -> list[str]:
        """사회적 증거(Social Proof) 모델 적용 훅 생성"""
        return self.generate_hooks("social_proof", product, count=count)

    def generate_authority_hooks(self, product: dict, count: int = 3) -> list[str]:
        """권위(Authority) 모델 적용 훅 생성"""
        return self.generate_hooks("authority", product, count=count)

    def generate_scarcity_hooks(self, product: dict, count: int = 3) -> list[str]:
        """희소성(Scarcity) 모델 적용 훅 생성"""
        return self.generate_hooks("scarcity", product, count=count)

    def generate_zeigarnik_hooks(self, product: dict, count: int = 3) -> list[str]:
        """자이가르닉(Zeigarnik) 효과 모델 적용 훅 생성"""
        return self.generate_hooks("zeigarnik", product, count=count)

    def generate_multi_style_hooks(
        self,
        product: dict,
        pain_points: list[str] | None = None,
        styles: list[str] | None = None,
    ) -> dict[str, list[str]]:
        """
        여러 스타일의 후킹 문구 일괄 생성

        Args:
            product: 제품 정보
            pain_points: 페인포인트 목록
            styles: 생성할 스타일 목록 (None이면 전체)

        Returns:
            {스타일: [후킹문구들]} 딕셔너리
        """
        if styles is None:
            styles = list(HOOK_STYLES.keys())

        results = {}
        for style in styles:
            results[style] = self.generate_hooks(
                style=style,
                product=product,
                pain_points=pain_points,
                count=2,  # 각 스타일당 2개
            )

        return results

    async def generate_ai_hooks(
        self,
        product: dict,
        pain_points: list[str],
        target_audience: dict,
        count: int = 5,
    ) -> list[str]:
        """
        AI(Gemini)를 활용한 맞춤 후킹 문구 생성

        Args:
            product: 제품 정보
            pain_points: 고객 페인포인트
            target_audience: 타겟 오디언스 정보
            count: 생성할 후킹 수

        Returns:
            AI가 생성한 후킹 문구 리스트
        """
        if not self._gemini:
            # AI 클라이언트 없으면 템플릿 기반으로 폴백
            return self.generate_hooks("curiosity", product, pain_points, count)

        prompt = f"""
### 🤖 Role: AI-Powered Short-form Hook Generator
You are an advanced AI system trained on millions of high-performing short-form video ads.
Your specialty: generating hooks that achieve 15%+ CTR by leveraging psychological triggers derived from real customer pain points.

### 🎯 Objective
Generate exactly {count} diverse, scroll-stopping Korean hook phrases.
Each hook should apply a DIFFERENT psychological strategy to maximize A/B testing value.

### 📦 Product Intelligence
- **Product Name:** {product.get("name", "N/A")}
- **Category:** {product.get("category", "N/A")}
- **Core Benefit:** {product.get("benefit", "N/A")}

### 👥 Target Audience Profile
- **Primary Persona:** {target_audience.get("primary", "일반 소비자")}
- **Pain Points (Voice of Customer):** {", ".join(pain_points[:3]) if pain_points else "데이터 없음"}
*⚠️ CRITICAL: Pain points are extracted from REAL customer feedback. Weave their exact language into hooks.*

### 🧠 Psychological Strategy Mix (Apply One Per Hook)
1. **Curiosity Gap:** Hint at valuable info without revealing ("이거 모르면...")
2. **Loss Aversion:** Emphasize what they'll lose by NOT acting ("안 쓰면 손해")
3. **Social Proof:** Numbers, popularity, reviews ("10만 명이 선택")
4. **Urgency/Scarcity:** Time pressure, limited availability ("오늘만", "품절 임박")
5. **Negativity Bias:** Shock, fear, worst case ("자면서 00 먹을 확률")

### 📋 Hook Quality Criteria (CRITICAL)
- **Length:** 10-15 Korean characters MAXIMUM
- **First 3 Characters:** Must trigger emotion immediately
- **Emoji Usage:** ONE strategic emoji per hook (at start or end)
- **Tone:** Colloquial, like a friend's urgent text message
- **Diversity:** Each hook must use a DIFFERENT strategy from the list above

### ✨ Few-Shot Examples (Top Performers)
- 🤔 (Curiosity): "99%가 모르는 비밀"
- 😱 (Negativity): "방치하면 이렇게 됨"
- ⚡ (Urgency): "오늘 끝. 서두르세요"
- 👥 (Social Proof): "후기 폭발, 품절 임박"
- 💡 (Benefit): "뿌리자마자 순삭"

### 📤 Output Format (STRICT)
- One hook per line
- Include exactly ONE emoji per hook
- NO numbers, bullets, or explanations
- Plain text ONLY

### ✨ Now generate {count} high-converting, psychologically diverse hooks.
"""
        log_llm_request("AI 훅 생성", f"제품: {product.get('name', 'N/A')}, {count}개")
        try:
            response = await self._gemini.generate_text_async(prompt)
            hooks = [line.strip() for line in response.split("\n") if line.strip()]
            hooks = hooks[:count]
            log_llm_response("AI 훅 생성", f"{len(hooks)}개 생성 완료")
            return hooks
        except Exception as e:
            log_llm_fail("AI 훅 생성", str(e))
            logger.warning(f"AI 후킹 생성 실패, 템플릿 사용: {e}")
            return self.generate_hooks("curiosity", product, pain_points, count)

    def get_best_hooks_for_video(
        self,
        product: dict,
        video_style: str = "dramatic",
        pain_points: list[str] | None = None,
    ) -> list[dict]:
        """
        비디오 스타일에 맞는 최적의 후킹 조합 반환

        Args:
            product: 제품 정보
            video_style: 비디오 스타일 (dramatic, calm, horror 등)
            pain_points: 페인포인트

        Returns:
            [{style, hook, recommended_for}] 리스트
        """
        # 비디오 스타일별 추천 후킹 스타일
        style_mapping = {
            "dramatic": ["urgency", "reversal", "negativity"],
            "calm": ["question", "curiosity", "social_proof"],
            "horror": ["negativity", "urgency", "question"],
            "commercial": ["curiosity", "social_proof", "reversal"],
        }

        recommended_styles = style_mapping.get(
            video_style, ["curiosity", "negativity", "question"]
        )

        results = []
        for style in recommended_styles:
            style_key = style if style in HOOK_STYLES else "curiosity"
            hooks = self.generate_hooks(style_key, product, pain_points, count=1)
            if hooks:
                results.append(
                    {
                        "style": style_key,
                        "style_name": HOOK_STYLES[style_key]["name"],
                        "hook": hooks[0],
                        "recommended_for": video_style,
                    }
                )

        return results

    async def generate_psychological_ab_test(
        self,
        product: dict,
        pain_points: list[str],
        count: int = 4,
    ) -> list[dict]:
        """
        다차원 심리 기제 기반 A/B 테스트용 훅 세트 생성
        """
        if not self._gemini:
            # 폴백: 기본 스타일들로 생성
            styles = ["loss_aversion", "benefit", "curiosity", "social_proof"]
            results = []
            for i, style in enumerate(styles[:count]):
                h = self.generate_hooks(style, product, pain_points, count=1)
                results.append(
                    {
                        "hook": h[0] if h else "핵심 훅",
                        "strategy": style,
                        "rationale": "기본 전략 적용",
                    }
                )
            return results

        prompt = f"""
### 🤖 Role: Advanced Marketing Psychologist & Copywriter
You are an expert in behavioral economics and conversion-centered design.
Your task is to generate {count} distinct hooks, each leveraging a fundamentally different psychological lever for A/B testing.

### 📦 Product Context
- **Name:** {product.get("name", "N/A")}
- **Core Benefit:** {product.get("benefit", "N/A")}
- **Pain Points:** {", ".join(pain_points[:3]) if pain_points else "N/A"}

### 🎯 Objective: Multi-Pillar A/B Strategy
Generate exactly {count} hooks covering these specific pillars:
1. **Fear/Pain (Pillar A):** What do they lose? What happens if they don't buy? (Loss Aversion)
2. **Gain/Dream (Pillar B):** What is the instant positive transformation? (Benefit focus)
3. **Logic/Proof (Pillar C):** Why should they trust you? (Social Proof/Numbers)
4. **Curiosity (Pillar D):** What's the hidden secret? (Zeigarnik Effect)

### 📤 Output Format (Strict JSON)
Output ONLY a JSON list of objects:
[
  {{
    "hook": "Korean hook text (short, punchy)",
    "strategy": "Pillar name (Fear, Gain, Logic, or Curiosity)",
    "rationale": "Brief English explanation of why this specific psychological trigger was used."
  }}
]
"""
        try:
            response = await self._gemini.generate_text_async(prompt)
            # JSON 파싱
            import json
            import re

            text = response.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Psychological A/B test generation failed: {e}")
            return []

    async def generate_trend_hooks(
        self,
        product: dict,
        count: int = 3,
        rag_client: Any = None,
        length: str = "long",  # short, medium, long
    ) -> list[str]:
        """
        RAG 기반 실시간 트렌드 반영 훅 생성 (밈, 뉴스, 이슈)
        """
        if not self._gemini or not rag_client:
            return self.generate_hooks("curiosity", product, count=count)

        # 1. 트렌드/밈 검색 (RAG)
        # 제품 카테고리와 관련된 최신 트렌드를 검색
        category = product.get("category", "")
        keywords = product.get("keywords", [])
        # 검색 쿼리 확장: 단순 카테고리뿐만 아니라 범용적인 밈 트렌드도 검색
        search_queries = [
            f"{category} 트렌드 이슈 {datetime.now().year}",
            "유튜브 쇼츠 유행어 밈",
            "인스타 릴스 챌린지 트렌드",
            "최신 유행하는 짤방 드립",
        ]

        rag_context_lines = []
        for q in search_queries:
            results = rag_client.search(q, max_results=2)
            for item in results:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                rag_context_lines.append(f"- {title}: {snippet}")

        trend_context = (
            "\n".join(rag_context_lines)
            if rag_context_lines
            else "특이 트렌드 없음. 일반적인 대세감 활용."
        )

        log_step(
            "트렌드 검색",
            str(search_queries),
            f"{len(rag_context_lines)}건 컨텍스트 확보",
        )

        # 길이 옵션에 따른 글자 수 제한 설정
        length_guide = "Medium (20-30 chars)"
        if length == "short":
            length_guide = "Short (under 20 chars)"
        elif length == "long":
            length_guide = "Long (30-45 chars)"

        # 2. 트렌드 반영 훅 생성 (LLM)
        prompt = f"""
### 🤖 Role: Viral Trend Hunter & Meme Specialist (Korea)
You are a social media trend expert who knows exactly what memes and slang are viral in Korea RIGHT NOW (2024-2025).
Your goal is to seamlessly blend the product into the hottest current trends to create viral hooks.

### 📦 Product Info
- **Name:** {product.get("name")}
- **Category:** {category}
- **Benefit:** {product.get("benefit")}

### 🌍 Real-time Trend Context (from RAG)
{trend_context}

### 🎯 Objective
Generate exactly {count} trendy, meme-based hooks in Korean.
- **Aggressively use recent memes** (e.g., Kim Dong-hyun 'Stun Gun/Cicada', 'Frozen Han River cat', 'Doremi Market', 'Physical: 100' vibes) if they fit the vibe.
- Use the provided RAG context if relevant.
- Tone: Extremely online, Gen-Z, witty, fast-paced, high-dopamine.

### 📋 Rules
- Length: {length_guide}
- ONE Emoji per hook
- **Parody existing memes** creatively.
- Format: Plain text, one per line

### ✨ Style Reference (Recent Vibes)
- "대전 아저씨(김동현)도 놀랄 {category} 효과 ㄷㄷ" (Memetic comparison)
- "꽁꽁 얼어붙은 {category} 위로 고양이가..." (Trending format)
- "너 T야? {category} 안 쓰는 T..." (Personality meme)
- "폼 미쳤다... {product} 이거 실화?" (Slang)

### ✨ Now generate {count} viral meme hooks.
"""
        try:
            response = await self._gemini.generate_text_async(prompt)
            hooks = [line.strip() for line in response.split("\n") if line.strip()]
            hooks = [h for h in hooks if not h.startswith(("1.", "-", "*"))][:count]
            # 클렌징이 덜 됐을 수 있으니 한번 더
            final_hooks = []
            for h in hooks:
                clean = h.lstrip("0123456789. -*")
                final_hooks.append(clean)

            if final_hooks:
                log_success(f"{len(final_hooks)}개 트렌드 훅 생성 완료")
                return final_hooks
            else:
                return self.generate_hooks("social_proof", product, count=count)

        except Exception as e:
            logger.error(f"Trend hook generation failed: {e}")
            return self.generate_hooks("social_proof", product, count=count)
