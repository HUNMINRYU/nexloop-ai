"""
Google Veo 3.1 Prompt Engine
Applied Skill: prompt-engineering (CO-STAR Framework)
"""


class VeoPromptEngine:
    """
    Veo 3.1 프롬프트 엔지니어링 엔진

    [Prompt Engineering Principles Applied]
    1. CO-STAR Framework (Context, Objective, Style, Tone, Audience, Response)
    2. Defense in Depth (Safety & Trademark Guardrails)
    3. Few-Shot Prompting (Examples)
    4. Chain of Thought (Internal Reasoning allowed in System Prompt, but Output is strict)
    """

    SYSTEM_CONTEXT = """
### 🤖 Role
You are a **Senior Cinematic Director & Veo 3.1 Prompt Strategist**.
You translate marketing concepts into precise, photorealistic, and visually breathtaking video prompts.

### 🎯 Objective
Create a high-fidelity video prompt for Google Veo 3.1. Treat the output like a production script that directs the camera, lighting, and movement without relying on on-screen text.

### 🛡️ Safety & Policy Guardrails (CRITICAL)
1. **No Real Names:** Use generic descriptions (e.g., "A charismatic chef").
2. **No Trademarks:** Use "generic smartphone", "unbranded laptop".
3. **No NSFW:** Strictly no violence, gore, sexual content, or hate speech.
4. **NO TEXT:** Do not include any instructions for on-screen text, logos, or watermarks. The visuals must tell the story without typography.

### 🎨 Cinematic Prompt Ingredients
Every prompt must weave together:
- **Subject & Action:** Detailed description of 'who' and 'what'.
- **Cinematic Style:** Photorealistic, 4k, film-like texture.
- **Camera Work:** Specific angles and lens movements (e.g., "slow dolly-in on 35mm lens").
- **Lighting & Atmosphere:** Mood-setting lighting (e.g., "chiaroscuro", "volumetric lighting").
- **Environment:** Rich setting details.
"""

    @staticmethod
    def get_prompt_structure() -> str:
        return """
### 📝 Response Format (Strict JSON)
{
    "veo_prompt": "A cohesive directorial paragraph in English...",
    "negative_prompt": "text, watermark, typography, font, blurry, distorted, morphing...",
    "metadata": {
        "style": "Cinematic/Minimal/etc",
        "camera_motion": "Pan Right/Zoom In/etc",
        "mood": "Energetic/Calm/etc"
    }
}
"""

    @staticmethod
    def get_few_shot_examples() -> str:
        return """
### ✨ Few-Shot Examples

**Input:**
Product: "GlowUp Serum" (Skincare)
Hook: "3일 만에 달라지는 피부 기적"
Style: "Clean & Minimal"

**Output:**
{
    "veo_prompt": "A cinematic close-up of a premium glass dropper bottle containing golden serum, resting on a white marble surface. Soft morning sunlight filters through a window, casting long, elegant shadows. A slow dolly-in using a 35mm lens reveals microscopic air bubbles in the serum. No text, watermark-free, pure visual high-fidelity aesthetics.",
    "negative_prompt": "text, watermark, branding, letters, blurry, distorted hand, bad nails, low quality, dark, grainy",
    "metadata": {
        "style": "Minimal",
        "camera_motion": "Dolly In",
        "mood": "Pure & Clean"
    }
}

**Input:**
Product: "TurboX Gaming Mouse" (Tech)
Hook: "게이머를 위한 궁극의 무기"
Style: "Cyberpunk"

**Output:**
{
    "veo_prompt": "Dynamic low-angle tracking shot of a sleek black gaming mouse with RGB edges pulsing in neon magenta. The scene is set in a dark, atmospheric room with volumetric blue fog. Cyberpunk city lights reflect off the mouse's matte surface. Cinematic depth of field, 4k photorealistic, sharp focus on the scroll wheel. Zero text or logos.",
    "negative_prompt": "text, typography, logo, blurry, distorted, messy cables, dust, low resolution, flickering",
    "metadata": {
        "style": "Cyberpunk",
        "camera_motion": "Low-angle Tracking",
        "mood": "Futuristic & Energetic"
    }
}
"""

    @classmethod
    def construct_generation_prompt(
        cls,
        product_name: str,
        product_desc: str,
        hook_text: str,
        style: str = "Cinematic",
    ) -> str:
        """
        Generates the full prompt to be sent to the LLM (Gemini)
        to ask IT to write the Veo prompt.
        """
        base_prompt = f"""
{cls.SYSTEM_CONTEXT}

{cls.get_prompt_structure()}

{cls.get_few_shot_examples()}

### 🎬 Current Task
**Input:**
Product: "{product_name}" ({product_desc})
Hook: "{hook_text}"
Style: "{style}"

**Action:**
Write the optimally engineered prompt for Google Veo 3.1.
Ensure the prompt visualizes the 'Hook' concept creatively.
"""
        return base_prompt

    @staticmethod
    def get_prompt_example(style: str = "Cinematic") -> dict[str, str]:
        """UI에 표시할 예시 프롬프트 반환"""
        if style == "Cinematic":
            return {
                "veo_prompt": "Cinematic wide shot of a luxury car driving through a coastal road at sunset...",
                "negative_prompt": "blur, distortion, low quality",
            }
        return {
            "veo_prompt": "Studio shot of a product on a clean background...",
            "negative_prompt": "clutter, messy, dark",
        }
