import json
import re
from collections.abc import Callable
from typing import Optional

from config.products import get_product_by_name
from core.exceptions import ThumbnailGenerationError
from core.interfaces.ai_service import IMarketingAIService
from utils.logger import get_logger, log_llm_fail, log_llm_request, log_llm_response, log_step, log_success

logger = get_logger(__name__)

# 제품·설명 출처: config/products.py (BLUEGUARD_PRODUCTS), get_product_by_name(name) → Product
# Product: name, category, description, target, visual_description(선택)
# API: GET /products → 이름 목록, GET /products/{product_name} → 상세(description 포함)


# === 썸네일 스타일 프리셋 (9종 최적화) ===
THUMBNAIL_STYLES = {
    # 1. [감정] 찐후기 (얼굴 필수)
    "raw_authentic": {
        "name": "리얼리즘 (얼굴)",
        "prompt_modifier": "selfie shot of an everyday person holding the product, authentic messy home background, raw unfiltered skin texture, direct eye contact, emotional expression (shock or relief), UGC style, shot on iPhone",
        "colors": "natural lighting, real life colors",
    },
    # 2. [체험] 1인칭 손 (얼굴 금지)
    "hand_grip": {
        "name": "핸드 그립 (POV)",
        "prompt_modifier": "first-person point of view (POV) shot, a hand tightly gripping the product, close-up focus on hand and product, blurred background, user experience feel, no faces",
        "colors": "skin tones, product colors, soft blur",
    },
    # 3. [증명] 소셜/리뷰 (UI 요소)
    "social_proof": {
        "name": "소셜 프루프 (리뷰)",
        "prompt_modifier": "product placed on a table with floating social media notification bubbles, '5-star rating' icons, text message overlay saying 'It works!', blurred cozy home background, mobile interface aesthetic",
        "colors": "soft blurred background, bright notification colors (green/blue)",
    },
    # 4. [기술] 투시/탐지 (특수효과)
    "tech_vision": {
        "name": "테크 비전 (X-ray)",
        "prompt_modifier": "split screen or circular zoom lens effect. Showing 'hidden' bugs revealed by the product, thermal vision or x-ray green/red tint overlay, high-tech analysis vibe, visualizing the invisible problem",
        "colors": "neon green, dark tech background, heat map colors",
    },
    # 5. [결과] 비교 (분할)
    "before_after": {
        "name": "비포 & 애프터",
        "prompt_modifier": "split screen comparison with distinct dividing line. Left side: dirty/infested/dark (Before). Right side: clean/safe/bright (After). Visual proof, dramatic contrast",
        "colors": "dark grey vs bright white/blue",
    },
    # 6. [혜택] 경고/세일 (그래픽)
    "bold_sale": {
        "name": "프로모션 (세일)",
        "prompt_modifier": "heavy promotional poster design, danger tape patterns, diagonal layout, high contrast warning style, urgent atmosphere, hard shadows",
        "colors": "bright red, yellow, black warning colors",
    },
    # 7. [트렌드] 힙/스티커 (아트)
    "neobrutalism": {
        "name": "네오브루탈리즘",
        "prompt_modifier": "neo-brutalism design, flat 2D sticker art, thick black outlines, brutalist layout, high contrast, collage style, trendy aesthetic, no gradients",
        "colors": "hot pink, electric blue, lime green, white",
    },
    # 8. [고급] 제품 정면 (깔끔)
    "studio_hero": {
        "name": "스튜디오 히어로",
        "prompt_modifier": "premium product photography, hero shot centered, perfect studio lighting, clean solid or gradient background, sharp focus, 4k resolution, advertising standard, no props",
        "colors": "clean white, grey, or brand color background",
    },
    # 9. [권위] 전문가 (신뢰)
    "professional": {
        "name": "프로페셔널 (신뢰)",
        "prompt_modifier": "professional model in business suit holding the product, modern office background, soft studio lighting, confident posture, trusted expert look, high-end commercial photography",
        "colors": "navy, charcoal, white, gold accents",
    },
}

# 스타일별 카피 톤앤매너 지침 (extract_visual_info용)
STYLE_COPY_GUIDE = """
- raw_authentic (리얼리즘): 친구에게 카톡 보내듯 짧고 감정적인 구어체. (예: "와.. 이거 진짜네?", "헐, 벌레 다 사라짐", "속는 셈 쳤는데 대박")
- hand_grip (핸드그립): 사용자가 직접 느끼는 효능 중심의 짧은 감탄사. 1인칭 시점. (예: "뿌리자마자 순삭", "내돈내산 종결템", "이거 물건이네")
- social_proof (소셜프루프): 리뷰, 별점, 알림 메시지 느낌. (예: "재구매율 1위", "⭐⭐⭐⭐⭐", "후기 9,999+ 돌파", "배송 시작 알림")
- tech_vision (테크비전): 기술적이고 분석적인 짧은 단어. (예: "숨은 해충 탐지", "침투력 99.9%", "원천 차단 기술")
- before_after (비포애프터): 결과와 변화를 강조하는 직관적 문구. (예: "단 3일의 변화", "뿌리기 전 vs 후", "방치하면 이렇게 됨")
- bold_sale (프로모션): 긴급하고 자극적인 혜택 강조. (예: "오늘만 50%", "곧 품절 임박", "1+1 마지막 기회", "사장님이 미쳤어요")
- neobrutalism (네오브루탈): MZ세대 타겟의 힙하고 짧은 단어, 반말 가능. (예: "벌레 컷.", "이거면 끝.", "킹성비 갑", "해충 박멸")
- studio_hero (스튜디오): 제품명이나 핵심 가치를 깔끔하게 명사형으로. (예: "프리미엄 방역", "벅스델타", "압도적 성능")
- professional (프로페셔널): 정중하고 신뢰감 있는 권위적인 어조. (예: "전문가 강력 추천", "방역 업체 사용", "약국 동일 성분")
""".strip()


class ThumbnailService:
    """썸네일 생성 서비스"""

    def __init__(self, client: IMarketingAIService) -> None:
        self._client = client

    def get_available_styles(self) -> list[dict]:
        """사용 가능한 스타일 목록 반환"""
        return [
            {
                "key": key,
                "name": style["name"],
                "description": style["prompt_modifier"][:50] + "...",
            }
            for key, style in THUMBNAIL_STYLES.items()
        ]

    def generate(
        self,
        product: dict,
        hook_text: str,
        style: str = "neobrutalism",
        include_text_overlay: bool = False,
        accent_color: str | None = None,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> bytes | None:
        """
        썸네일 생성

        Args:
            product: 제품 정보
            hook_text: 후킹 문구
            style: 스타일 키
            include_text_overlay: 텍스트 오버레이 포함 여부
            accent_color: 강조 색상
            progress_callback: 진행 콜백
        """
        log_step("썸네일 생성", "시작", f"제품: {product.get('name', 'N/A')}, 훅: {hook_text[:20]}..., 스타일: {style}")

        try:
            prompt = self._build_thumbnail_prompt(
                product=product,
                hook_text=hook_text,
                style=style,
                include_text_overlay=include_text_overlay,
                accent_color=accent_color,
            )
            result = self._client.generate_image(prompt=prompt, aspect_ratio="9:16")

            if result:
                log_success(f"썸네일 생성 완료: {len(result):,} bytes")
                return result

            raise ThumbnailGenerationError("썸네일 생성 결과가 없습니다.")

        except ThumbnailGenerationError:
            raise
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {e}")
            raise ThumbnailGenerationError(
                f"썸네일 생성 실패: {e}",
                original_error=e,
            )

    def generate_neobrutalism(
        self,
        product: dict,
        hook_text: str,
        accent_color: str = "yellow",
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> bytes | None:
        """
        네오브루탈리즘 스타일 썸네일 생성

        Args:
            product: 제품 정보
            hook_text: 후킹 문구
            accent_color: 강조 색상
            progress_callback: 진행 콜백
        """
        return self.generate(
            product=product,
            hook_text=hook_text,
            style="neobrutalism",
            include_text_overlay=True,
            accent_color=accent_color,
            progress_callback=progress_callback,
        )

    def generate_multiple(
        self,
        product: dict,
        hook_texts: list[str],
        styles: list[str] | None = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """여러 스타일 썸네일 일괄 생성"""
        log_step("썸네일 일괄 생성", "시작", f"{len(hook_texts)}개")

        if styles is None:
            styles = ["neobrutalism"] * len(hook_texts)

        results = []
        total = len(hook_texts) if hook_texts else 1

        for i, hook_text in enumerate(hook_texts):
            style_key = styles[i % len(styles)]
            if progress_callback:
                progress = int((i / total) * 100)
                progress_callback(f"썸네일 {i + 1}/{total} 생성 중...", progress)

            image = self.generate(
                product=product,
                hook_text=hook_text,
                style=style_key,
                include_text_overlay=True,
            )
            if image:
                results.append(
                    {
                        "image": image,
                        "hook_text": hook_text,
                        "style": style_key,
                        "style_name": THUMBNAIL_STYLES.get(style_key, {}).get("name", style_key),
                    }
                )

        if progress_callback:
            progress_callback("모든 썸네일 생성 완료!", 100)

        log_success(f"썸네일 일괄 생성 완료: {len(results)}개")
        return results

    def _build_thumbnail_prompt(
        self,
        product: dict,
        hook_text: str,
        style: str,
        include_text_overlay: bool,
        accent_color: Optional[str],
    ) -> str:
        product_name = product.get("name", "Product")
        category = product.get("category", "Item")
        visual_desc = product.get("visual_description") or "generic product packaging"

        style_config = THUMBNAIL_STYLES.get(
            style, THUMBNAIL_STYLES["neobrutalism"]
        )
        base_prompt = style_config["prompt_modifier"]
        colors = (
            accent_color
            if (style == "neobrutalism" and accent_color)
            else style_config["colors"]
        )

        if include_text_overlay:
            text_container_map = {
                "raw_authentic": "as UGC-style sticker text, bold white with black outline",
                "hand_grip": "as a floating sticker near the hand",
                "social_proof": "inside a chat bubble or notification box",
                "tech_vision": "inside a high-tech HUD style text box",
                "before_after": "on a semi-transparent bar or label, bold sans-serif",
                "bold_sale": "inside a bright yellow caution-tape style text banner",
                "neobrutalism": "inside a white rectangular sticker-style text box with black border",
                "studio_hero": "as a clean bold title below or overlay on the hero shot, minimal and high-end",
                "professional": "on a semi-transparent dark overlay for contrast",
                "default": "inside a semi-transparent dark text box for readability",
            }
            container = text_container_map.get(
                style, text_container_map["default"]
            )
            text_instruction = (
                f'Text Overlay: Write "{hook_text}" {container}. '
                "Font: Bold Sans-serif. Ensure text is distinct, sharp, and 2D flat layer on top. "
                "Do not blend text with background."
            )
        else:
            text_instruction = (
                "No text, focus on visual imagery and composition."
            )

        full_prompt = (
            f"A vertical YouTube Shorts thumbnail. "
            f"Subject: {visual_desc} representing {product_name} ({category}). "
            f"Style: {base_prompt}. "
            f"Colors: {colors}. "
            f"**{text_instruction}** "
            "Composition: Centered subject, safe zone for UI at top and bottom. "
            "Quality: 8k, highly detailed, professional commercial finish."
        )
        prompt_escaped = full_prompt.replace("\\", "\\\\").replace('"', '\\"')

        settings_negative = (
            "--no blurry text --no double text --no ghosting "
            "--no youtube interface --no search bar --no phone battery icon "
            "--no ui elements --no distorted hands --ar 9:16"
        )

        return (
            "{\n"
            '  "model": "nano-banana",\n'
            f'  "prompt": "{prompt_escaped}",\n'
            '  "ratio": "9:16",\n'
            '  "upscale": "Upscale photos to high resolution x2",\n'
            f'  "settings": "{settings_negative}"\n'
            "}"
        ).strip()

    def generate_ab_test_set(
        self,
        product: dict,
        hook_text: str,
        styles: list[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """
        A/B 테스트용 다양한 스타일 썸네일 세트 생성

        Args:
            product: 제품 정보
            hook_text: 공통 훅 텍스트
            styles: 테스트할 스타일 목록 (None이면 전체)

        Returns:
            [{style, image_bytes, description}] 리스트
        """
        if styles is None:
            styles = ["neobrutalism", "raw_authentic", "hand_grip"]

        results = []
        for i, style in enumerate(styles):
            if progress_callback:
                progress_callback(
                    f"스타일 {i + 1}/{len(styles)} 생성 중...",
                    int((i / len(styles)) * 100),
                )

            try:
                image = self.generate(
                    product=product,
                    hook_text=hook_text,
                    style=style,
                )
                results.append(
                    {
                        "style": style,
                        "style_name": THUMBNAIL_STYLES.get(style, {}).get(
                            "name", style
                        ),
                        "image_bytes": image,
                        "description": THUMBNAIL_STYLES.get(style, {}).get(
                            "prompt_modifier", ""
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"스타일 {style} 생성 실패: {e}")

        return results

    def generate_from_strategy(
        self,
        product: dict,
        strategy: dict,
        count: int = 3,
        styles: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """전략 기반 썸네일 생성"""
        # 전략에서 훅 텍스트 추출
        # 전략에서 훅 텍스트 추출 (Dict/Str 혼용 지원)
        raw_hooks = strategy.get("hook_suggestions", [])
        hooks = []
        for h in raw_hooks:
            if isinstance(h, dict):
                h_text = h.get("hook")
                if h_text:
                    hooks.append(h_text)
            elif h:
                hooks.append(str(h))
        
        if not hooks:
            hooks = [f"{product.get('name', '제품')} 지금 바로!"]

        hook_texts = hooks[:count]

        return self.generate_multiple(
            product=product,
            hook_texts=hook_texts,
            styles=styles,
            progress_callback=progress_callback,
        )

    def extract_visual_info(self, raw_description: str) -> dict:
        """
        상품 설명을 분석하여 시각적 묘사·후킹 문구·추천 스타일을 추출합니다.
        먼저 추천 스타일을 정한 뒤, 그 스타일에 맞는 톤앤매너의 hook_text를 생성합니다.
        LLM(Gemini)이 있으면 사용하고, 없거나 실패 시 키워드 기반 폴백을 사용합니다.
        """
        style_keys = list(THUMBNAIL_STYLES.keys())
        default_info = {
            "name": "상품",
            "category": "General",
            "visual_description": "generic product packaging",
            "hook_text": "지금 구매하세요!",
            "recommended_style": "neobrutalism",
        }

        if hasattr(self._client, "generate_text"):
            prompt = f"""### 🤖 Role: Marketing Art Director & Visual Copywriter
You are an expert marketing art director with a keen eye for visual storytelling and a mastery of conversion-focused copywriting.
Your specialty: transforming product descriptions into compelling visual concepts that drive clicks and conversions.

### 🎯 Objective
Analyze the product description below and output a JSON object containing:
1. **recommended_style**: The BEST thumbnail style from the provided keys
2. **hook_text**: A Korean hook phrase (12 chars max) that PERFECTLY matches the tone of the selected style
3. **visual_description**: An English prompt for image generation (product appearance only)

### 📦 Product Description to Analyze
{raw_description}

### 🎨 Available Style Keys (Use Exactly As-Is)
{style_keys}

### 📋 Style-Specific Copy Tone Guide (CRITICAL)
{STYLE_COPY_GUIDE}

### ✨ Few-Shot Examples (Quality Reference)
**Example 1: Pest Control Product**
- Input: "바퀴벌레를 순식간에 박멸하는 강력한 살충제"
- Output: {{"recommended_style": "negativity", "hook_text": "방치하면 이렇게 됨", "visual_description": "white plastic spray bottle with green toxic warning label, held by hand, dark kitchen background with shadow of roach"}}

**Example 2: Beauty Serum**
- Input: "3일 만에 피부가 달라지는 프리미엄 세럼"
- Output: {{"recommended_style": "studio_hero", "hook_text": "3초 물광 피부", "visual_description": "luxury glass dropper bottle with gold cap and glowing liquid inside, soft studio lighting, clean white background"}}

### 🧠 Decision Process (Think Step-by-Step)
1. **Identify Product Category:** What type of product is this? (Beauty? Tech? Household?)
2. **Match Emotional Tone:** Which style's tone best fits this product's value proposition?
3. **Craft Style-Matched Hook:** Write a hook that sounds native to the selected style's copy guide
4. **Visualize Product:** Describe ONLY the physical appearance (color, shape, material, setting)

### 📤 Output Format (STRICT - JSON ONLY)
{{
    "recommended_style": "style_key_from_list",
    "hook_text": "Korean hook text (max 12 chars, style-matched tone)",
    "visual_description": "English visual description for image generation (product appearance only)",
    "name": "Product Name (extracted or inferred)",
    "category": "Product Category"
}}

⚠️ CRITICAL: Output ONLY the JSON object. No markdown, no code blocks, no explanations.
"""
            log_llm_request("상품 설명 분석", f"설명 {len(raw_description)}자")
            try:
                response = self._client.generate_text(prompt, temperature=0.3)
                text = (response or "").strip()
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```\s*$", "", text)
                data = json.loads(text)
                # LLM은 3가지(visual_description, hook_text, recommended_style)만 반환; name/category는 기본값
                visual_description = data.get("visual_description") or default_info["visual_description"]
                hook_text = (data.get("hook_text") or default_info["hook_text"]).strip()
                recommended_style = (data.get("recommended_style") or "").strip() or default_info["recommended_style"]
                if recommended_style not in style_keys:
                    recommended_style = default_info["recommended_style"]
                log_llm_response(
                    "상품 설명 분석",
                    f"hook_text={hook_text}, recommended_style={recommended_style}, visual_description={visual_description[:40]}...",
                )
                return {
                    "name": data.get("name") or default_info["name"],
                    "category": data.get("category") or default_info["category"],
                    "visual_description": visual_description,
                    "hook_text": hook_text,
                    "recommended_style": recommended_style,
                }
            except (json.JSONDecodeError, AttributeError) as e:
                log_llm_fail("상품 설명 분석", str(e))
                logger.warning(f"LLM 시각 정보 파싱 실패, 폴백 사용: {e}")

        raw_lower = raw_description.strip().lower()
        if "벅스델타" in raw_description or "벅스델타" in raw_lower:
            logger.info("[STEP] 상품 설명 분석 - 키워드 폴백 (벅스델타)")
            return {
                "name": "벅스델타",
                "category": "Pest Control",
                "visual_description": "a white plastic spray bottle with a green label held by a hand",
                "hook_text": "바퀴벌레 박멸",
                "recommended_style": "raw_authentic",
            }
        if "화장품" in raw_description or "세럼" in raw_description or "글로우" in raw_description:
            logger.info("[STEP] 상품 설명 분석 - 키워드 폴백 (화장품/세럼)")
            return {
                "name": "글로우 세럼",
                "category": "Beauty",
                "visual_description": "a luxury glass dropper bottle with gold cap, glowing liquid inside",
                "hook_text": "3초 물광 피부",
                "recommended_style": "fresh_clean",
            }
        if "텀블러" in raw_description or "아쿠아" in raw_description or "얼음" in raw_description and "24" in raw_description:
            logger.info("[STEP] 상품 설명 분석 - 키워드 폴백 (텀블러)")
            return {
                "name": "아쿠아 텀블러",
                "category": "Beverage",
                "visual_description": "a sleek stainless steel tumbler with blue gradient finish, water droplets on surface, ice cubes nearby",
                "hook_text": "얼음 24시간 보존",
                "recommended_style": "fresh_clean",
            }
        logger.info("[STEP] 상품 설명 분석 - 기본값 폴백")
        return default_info

    def generate_from_description(
        self,
        raw_description: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """
        상품 설명 줄글만 넣으면 시각 정보를 추출한 뒤 썸네일을 생성합니다.
        """
        analyzed = self.extract_visual_info(raw_description)
        logger.info(f"상품 설명 분석 결과: {analyzed}")

        product = {
            "name": analyzed["name"],
            "category": analyzed["category"],
            "visual_description": analyzed["visual_description"],
        }
        return self.generate(
            product=product,
            hook_text=analyzed["hook_text"],
            style=analyzed["recommended_style"],
            include_text_overlay=True,
            progress_callback=progress_callback,
        )

    def generate_from_product_name(
        self,
        product_name: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """
        제품명만 넣으면 카탈로그에서 제품·설명을 가져와 시각 정보 추출 후 썸네일 생성.
        제품·설명 출처: config/products.py (get_product_by_name) → name, description, target, visual_description
        """
        product = get_product_by_name(product_name)
        if not product:
            raise ThumbnailGenerationError(
                f"제품을 찾을 수 없습니다: {product_name}"
            )
        raw_description = (
            f"{product.name}. {product.description}. 대상: {product.target}."
        )
        analyzed = self.extract_visual_info(raw_description)
        product_dict = (
            product.model_dump()
            if hasattr(product, "model_dump")
            else product.__dict__
        )
        category_val = getattr(
            product_dict.get("category"),
            "value",
            product_dict.get("category", "General"),
        )
        product_for_generate = {
            "name": product_dict.get("name", product_name),
            "category": category_val,
            "visual_description": product_dict.get("visual_description")
            or analyzed["visual_description"],
        }
        logger.info(
            f"제품명 기반 썸네일: {product_name} → 훅 '{analyzed['hook_text']}', 스타일 {analyzed['recommended_style']}"
        )
        return self.generate(
            product=product_for_generate,
            hook_text=analyzed["hook_text"],
            style=analyzed["recommended_style"],
            include_text_overlay=True,
            progress_callback=progress_callback,
        )
