"""
AWS Bedrock service for Nova LLM integration.
Handles preview and full reading generation with cost tracking.
"""

import boto3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from reference_knowledge import ASTROLOGY_REFERENCE, TAROT_REFERENCE, PALMISTRY_REFERENCE, VOICE_LIBRARY


class BedrockService:
    """Service for interacting with AWS Bedrock Nova models."""
    
    def __init__(self):
        """Initialize Bedrock client with AWS credentials from environment or AWS CLI."""
        # Get credentials from environment (will be None if not set)
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Build client kwargs
        client_kwargs = {
            'service_name': 'bedrock-runtime',
            'region_name': region
        }
        
        # Only add explicit credentials if they're set in .env
        if aws_access_key and aws_access_key != 'your_access_key_here':
            client_kwargs['aws_access_key_id'] = aws_access_key
            client_kwargs['aws_secret_access_key'] = aws_secret_key
        
        # Create client (will use AWS CLI credentials if explicit ones not provided)
        self.client = boto3.client(**client_kwargs)
        
        # Nova model IDs
        self.preview_model = os.getenv('BEDROCK_PREVIEW_MODEL', 'us.amazon.nova-lite-v1:0')
        self.full_model = os.getenv('BEDROCK_FULL_MODEL', 'us.amazon.nova-pro-v1:0')
        
        # Token limits
        self.preview_max_tokens = 200
        self.full_max_tokens = 1200
        
        # Cost tracking (approximate USD per 1000 tokens)
        self.costs = {
            'us.amazon.nova-lite-v1:0': {'input': 0.00006, 'output': 0.00024},
            'us.amazon.nova-pro-v1:0': {'input': 0.0008, 'output': 0.0032},
        }
    
    def _build_messages(
        self,
        system_prompt: str,
        user_content: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Build messages in Bedrock Converse API format.
        
        Args:
            system_prompt: System instructions
            user_content: User message content
            
        Returns:
            Tuple of (system_prompt, messages_list)
        """
        messages = [
            {
                "role": "user",
                "content": [{"text": user_content}]
            }
        ]
        return system_prompt, messages

    def _build_message_list(
        self,
        user_messages: List[str],
    ) -> List[Dict[str, Any]]:
        return [
            {
                "role": "user",
                "content": [{"text": message}],
            }
            for message in user_messages
        ]
    
    def _calculate_cost(
        self, 
        model_id: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """
        Calculate approximate cost for a completion.
        
        Args:
            model_id: Bedrock model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        if model_id not in self.costs:
            return 0.0
        
        cost_per_1k = self.costs[model_id]
        input_cost = (input_tokens / 1000) * cost_per_1k['input']
        output_cost = (output_tokens / 1000) * cost_per_1k['output']
        
        return round(input_cost + output_cost, 6)

    def invoke_text(
        self,
        *,
        model_id: str,
        system_prompt: str,
        user_messages: List[str],
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        messages = self._build_message_list(user_messages)
        try:
            response = self.client.converse(
                modelId=model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                },
            )
            output_text = response['output']['message']['content'][0]['text']
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            cost = self._calculate_cost(model_id, input_tokens, output_tokens)
            return {
                'text': output_text.strip(),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost,
                'model': model_id,
                'raw': response,
            }
        except Exception as e:
            raise RuntimeError(f"Bedrock text generation failed: {str(e)}")
    
    def _build_reference_block(self) -> str:
        return (
            "REFERENCE MATERIAL (use as grounding, not prediction):\n"
            f"{ASTROLOGY_REFERENCE}\n\n"
            f"{TAROT_REFERENCE}\n\n"
            f"{PALMISTRY_REFERENCE}\n\n"
            f"{VOICE_LIBRARY}"
        )

    def _build_anchor_list(
        self,
        astrology_facts: Dict[str, Any],
        tarot_cards: List[Dict[str, str]],
        palm_facts: Optional[List[Dict[str, str]]]
    ) -> List[str]:
        anchors: List[str] = []

        if astrology_facts.get("sun_sign"):
            anchors.append(f"Sun sign: {astrology_facts['sun_sign']}")
        if astrology_facts.get("moon_sign"):
            anchors.append(f"Moon sign: {astrology_facts['moon_sign']}")
        if astrology_facts.get("rising_sign"):
            anchors.append(f"Rising sign: {astrology_facts['rising_sign']}")
        if astrology_facts.get("dominant_element"):
            anchors.append(f"Dominant element: {astrology_facts['dominant_element']}")
        if astrology_facts.get("dominant_planet"):
            anchors.append(f"Dominant planet: {astrology_facts['dominant_planet']}")

        top_aspects = astrology_facts.get("top_aspects") or []
        for aspect in top_aspects:
            a = aspect.get("a")
            b = aspect.get("b")
            t = aspect.get("type")
            if a and b and t:
                anchors.append(f"Aspect: {a} {t} {b}")

        for card in tarot_cards:
            name = card.get("card") or card.get("name")
            if name:
                position = card.get("position")
                if position:
                    anchors.append(f"Tarot: {name} ({position})")
                else:
                    anchors.append(f"Tarot: {name}")

        if palm_facts:
            for feature in palm_facts:
                f_name = feature.get("feature")
                f_value = feature.get("value")
                if f_name and f_value:
                    anchors.append(f"Palm: {f_name} = {f_value}")

        return anchors

    def _format_anchors(self, anchors: List[str]) -> str:
        if not anchors:
            return "- None"
        return "\n".join(f"- {anchor}" for anchor in anchors)

    def _format_primary_anchors(self, anchors: List[str], count: int = 3) -> str:
        if not anchors:
            return "- None"
        primary = anchors[:count]
        return "\n".join(f"- {anchor}" for anchor in primary)

    def _voice_contract(self, short_form: bool = False) -> str:
        if short_form:
            return """VOICE CONTRACT:
- Write like a sharp, grounded human (not therapist-speak, not textbook-speak)
- Be specific and candid; name the tension directly
- Use active voice and concrete verbs
- Avoid cliches, soft filler, and vague reassurance
- Keep your phrasing bold and a little playful when it helps
- Keep a little edge: one short punchy line is encouraged"""
        return """VOICE CONTRACT:
- Sound grounded, direct, and real-world practical
- Keep personality: warm but not soft-focus, candid but not harsh
- Use specific language tied to the user's symbols and question
- Avoid generic affirmations and technical jargon
- Allow light wit in phrasing when it supports clarity
- Make strong calls instead of vague summaries
- Keep momentum: each section should make one clear point
- Include occasional punchy one-line sentences for rhythm"""

    def _prediction_contract(self, short_form: bool = False) -> str:
        if short_form:
            return """PREDICTION STYLE:
- Include one clear forward-looking call
- Use directional language: "is likely to", "will tend to", or "expect"
- Tie the call directly to provided anchors
- No guarantees, no certainty theater"""
        return """PREDICTION STYLE:
- Make 2-4 clear forward-looking calls across the reading
- Use directional language: "is likely to", "will tend to", or "expect"
- Tie each forecast to specific anchors from chart/cards/palm
- Keep forecasts grounded in behavior, relationships, and personal patterns
- No guarantees, no certainty theater, no medical/legal/investment claims"""

    def _flow_reading_schema(
        self,
        flow_type: str,
        include_palm: bool = True,
    ) -> List[Dict[str, str]]:
        if flow_type == "tarot_solo":
            return [
                {"delimiter": "OPENING", "id": "opening_invocation", "title": "OPENING", "instruction": "Frame the user's question through the tarot spread."},
                {"delimiter": "TAROT_FOUNDATION", "id": "tarot_narrative", "title": "TAROT NARRATIVE", "instruction": "Interpret each card and position with concrete meaning."},
                {"delimiter": "PATTERN_SYNTHESIS", "id": "integrated_synthesis", "title": "SYNTHESIS", "instruction": "Synthesize the card pattern into one clear thread."},
                {"delimiter": "GUIDANCE", "id": "reflective_guidance", "title": "GUIDANCE", "instruction": "Offer reflective guidance from the cards."},
                {"delimiter": "CLOSING", "id": "closing_prompt", "title": "CLOSING", "instruction": "Close with one grounded question."},
            ]
        if flow_type == "palm_solo":
            return [
                {"delimiter": "OPENING", "id": "opening_invocation", "title": "OPENING", "instruction": "Frame the question through the palm symbols."},
                {"delimiter": "PALM_FOUNDATION", "id": "palm_insight", "title": "PALM INSIGHT", "instruction": "Interpret major palm features and what they suggest."},
                {"delimiter": "INTEGRATION", "id": "integrated_synthesis", "title": "SYNTHESIS", "instruction": "Tie palm insights to current life patterns."},
                {"delimiter": "GUIDANCE", "id": "reflective_guidance", "title": "GUIDANCE", "instruction": "Offer practical reflection."},
                {"delimiter": "CLOSING", "id": "closing_prompt", "title": "CLOSING", "instruction": "Close with one grounded prompt."},
            ]
        if flow_type == "sun_moon_solo":
            return [
                {"delimiter": "OPENING", "id": "opening_invocation", "title": "OPENING", "instruction": "Frame the question through Sun and Moon dynamics."},
                {"delimiter": "SUN_MOON_FOUNDATION", "id": "astrological_foundation", "title": "SUN AND MOON FOUNDATION", "instruction": "Interpret Sun identity, Moon needs, and tension/fit."},
                {"delimiter": "INTEGRATION", "id": "integrated_synthesis", "title": "SYNTHESIS", "instruction": "Connect these dynamics to current themes."},
                {"delimiter": "GUIDANCE", "id": "reflective_guidance", "title": "GUIDANCE", "instruction": "Offer practical reflection."},
                {"delimiter": "CLOSING", "id": "closing_prompt", "title": "CLOSING", "instruction": "Close with one grounded prompt."},
            ]
        if flow_type == "daily_horoscope":
            return [
                {"delimiter": "OPENING", "id": "opening_invocation", "title": "TODAY'S THEME", "instruction": "State today's core theme clearly."},
                {"delimiter": "ASTRO_WEATHER", "id": "astrological_foundation", "title": "ASTRO WEATHER", "instruction": "Explain relevant placements/aspects simply."},
                {"delimiter": "FOCUS_ACTIONS", "id": "reflective_guidance", "title": "FOCUS FOR TODAY", "instruction": "Offer concrete focus points for today."},
                {"delimiter": "CLOSING", "id": "closing_prompt", "title": "CLOSING", "instruction": "End with one daily check-in question."},
            ]
        if flow_type == "lunar_new_year_solo":
            return [
                {"delimiter": "OPENING", "id": "opening_invocation", "title": "OPENING", "instruction": "Set the year-ahead framing."},
                {"delimiter": "YEAR_AHEAD", "id": "lunar_forecast", "title": "YOUR YEAR AHEAD", "instruction": "Describe opportunities and challenges for the year."},
                {"delimiter": "INTEGRATION", "id": "integrated_synthesis", "title": "SYNTHESIS", "instruction": "Tie the year theme to the user's question."},
                {"delimiter": "GUIDANCE", "id": "reflective_guidance", "title": "GUIDANCE", "instruction": "Give grounded, practical orientation."},
                {"delimiter": "CLOSING", "id": "closing_prompt", "title": "CLOSING", "instruction": "End with one focused prompt for the year."},
            ]
        if flow_type == "blessing_solo":
            return [
                {"delimiter": "OPENING", "id": "opening_invocation", "title": "OPENING", "instruction": "Acknowledge current context in plain language."},
                {"delimiter": "BLESSING", "id": "reflective_guidance", "title": "BLESSING", "instruction": "Provide a concise 2-3 sentence blessing."},
                {"delimiter": "CLOSING", "id": "closing_prompt", "title": "CLOSING", "instruction": "Close with one reflective line."},
            ]
        combined_schema = [
            {"delimiter": "OPENING_INVOCATION", "id": "opening_invocation", "title": "OPENING", "instruction": "Emotional engagement."},
            {"delimiter": "ASTROLOGICAL_FOUNDATION", "id": "astrological_foundation", "title": "ASTROLOGICAL FOUNDATION", "instruction": "Natal chart analysis."},
            {"delimiter": "TAROT_NARRATIVE", "id": "tarot_narrative", "title": "TAROT NARRATIVE", "instruction": "Cards woven together."},
            {"delimiter": "INTEGRATED_SYNTHESIS", "id": "integrated_synthesis", "title": "SYNTHESIS", "instruction": "Tie it all together."},
            {"delimiter": "REFLECTIVE_GUIDANCE", "id": "reflective_guidance", "title": "GUIDANCE", "instruction": "Awareness, not advice."},
            {"delimiter": "CLOSING_PROMPT", "id": "closing_prompt", "title": "CLOSING", "instruction": "Reflective question."},
        ]
        if include_palm:
            combined_schema.insert(
                3,
                {
                    "delimiter": "PALM_INSIGHT",
                    "id": "palm_insight",
                    "title": "PALM INSIGHT",
                    "instruction": "Use palm data when present.",
                },
            )
        return combined_schema

    def _parse_sections_by_schema(
        self,
        text: str,
        schema: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        section_map = {item["delimiter"]: item for item in schema}
        sections: List[Dict[str, str]] = []
        current: Optional[Dict[str, str]] = None
        current_text: List[str] = []

        for line in text.split('\n'):
            matched = None
            for delimiter, item in section_map.items():
                if f"---{delimiter}---" in line:
                    matched = item
                    break
            if matched:
                if current:
                    raw_text = '\n'.join(current_text).strip()
                    deep_text = None
                    if "DEEP_INSIGHT:" in raw_text:
                        parts = raw_text.split("DEEP_INSIGHT:", 1)
                        raw_text = parts[0].strip()
                        deep_text = parts[1].strip()
                    payload: Dict[str, str] = {
                        "id": current["id"],
                        "title": current.get("title", ""),
                        "text": raw_text,
                    }
                    if deep_text:
                        payload["deep_text"] = deep_text
                    sections.append(payload)
                current = matched
                current_text = []
            elif current:
                current_text.append(line)

        if current:
            raw_text = '\n'.join(current_text).strip()
            deep_text = None
            if "DEEP_INSIGHT:" in raw_text:
                parts = raw_text.split("DEEP_INSIGHT:", 1)
                raw_text = parts[0].strip()
                deep_text = parts[1].strip()
            payload = {
                "id": current["id"],
                "title": current.get("title", ""),
                "text": raw_text,
            }
            if deep_text:
                payload["deep_text"] = deep_text
            sections.append(payload)

        return sections

    def generate_preview_teaser(
        self,
        question: str,
        astrology_facts: Dict[str, Any],
        tarot_cards: List[Dict[str, str]],
        palm_facts: Optional[List[Dict[str, str]]] = None,
        flow_type: str = "combined",
    ) -> Dict[str, Any]:
        """
        Generate preview teaser using Nova Lite (cheap, fast).
        
        Args:
            question: User's question/intention
            astrology_facts: Computed astrology placements
            tarot_cards: Drawn tarot cards
            palm_facts: Optional palm reading features
            
        Returns:
            Dict with teaser_text, tokens used, and cost
        """
        # Build system prompt
        reference_block = self._build_reference_block()
        anchors = self._build_anchor_list(astrology_facts, tarot_cards, palm_facts)
        primary_anchors = self._format_primary_anchors(anchors, count=3)

        system_prompt = f"""You are an insightful metaphysical reader providing preview teasers.

CRITICAL RULES:
- Output ONLY 2-3 sentences (max 50 words)
- Reference available anchors from the list provided (prefer primary anchors first)
- Ground interpretations in the provided reference material
- Include one directional forecast (short and specific)
- Avoid generic reassurance
- NO generic phrases like "you are someone who" or vague affirmations
- Must feel specific to THIS person's data
- Do not invent symbols not present in the inputs
- Keep it deterministic in style: choose one central pattern and stay with it
- Avoid hedge-stacking ("maybe/perhaps/might" chains)
- Avoid technical or textbook language; write like a grounded, real person
- Use plain, relatable phrasing with grit and momentum

{self._voice_contract(short_form=True)}
{self._prediction_contract(short_form=True)}

TONE: Grounded, bold, relatable, with grit and a little fun.
FLOW TYPE: {flow_type}

{reference_block}"""

        # Build user message with data
        palm_section = ""
        if palm_facts:
            palm_section = f"\n\nPalm features detected:\n{json.dumps(palm_facts, indent=2)}"
        
        user_content = f"""Generate a preview teaser for this reading:

Question: "{question}"

Primary anchors (must use these first):
{primary_anchors}

All anchors available:
{self._format_anchors(anchors)}

Astrology placements:
{json.dumps(astrology_facts, indent=2)}

Tarot cards drawn:
{json.dumps(tarot_cards, indent=2)}{palm_section}

Generate a 2-3 sentence teaser that creates curiosity about what these elements reveal together while remaining grounded, specific, and human."""

        system, messages = self._build_messages(system_prompt, user_content)
        
        try:
            # Call Bedrock Converse API
            response = self.client.converse(
                modelId=self.preview_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": self.preview_max_tokens,
                    "temperature": 0.7,
                    "topP": 0.92
                }
            )
            
            # Extract response
            output_text = response['output']['message']['content'][0]['text']
            
            # Extract token usage
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            
            # Calculate cost
            cost = self._calculate_cost(self.preview_model, input_tokens, output_tokens)
            
            return {
                'teaser_text': output_text.strip(),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost,
                'model': self.preview_model
            }
            
        except Exception as e:
            raise RuntimeError(f"Bedrock preview generation failed: {str(e)}")
    
    def generate_full_reading(
        self,
        question: str,
        astrology_facts: Dict[str, Any],
        tarot_cards: List[Dict[str, str]],
        palm_facts: Optional[List[Dict[str, str]]] = None,
        style: str = "grounded",
        flow_type: str = "combined",
        include_palm: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate full 7-section reading using Nova Pro.
        
        Args:
            question: User's question/intention
            astrology_facts: Computed astrology placements
            tarot_cards: Drawn tarot cards
            palm_facts: Optional palm reading features
            style: Reading style (grounded/mystical/direct)
            
        Returns:
            Dict with sections, tokens used, and cost
        """
        # Build system prompt with schema
        reference_block = self._build_reference_block()
        anchors = self._build_anchor_list(astrology_facts, tarot_cards, palm_facts)
        primary_anchors = self._format_primary_anchors(anchors, count=3)
        schema = self._flow_reading_schema(flow_type, include_palm=include_palm)
        schema_lines = "\n".join(
            f"- {idx + 1}. {item['delimiter']} ({item['instruction']})"
            for idx, item in enumerate(schema)
        )
        format_lines = "\n\n".join(
            f"---{item['delimiter']}---\n[text here]" for item in schema
        )

        system_prompt = f"""You are an insightful metaphysical reader creating personalised readings.

STYLE: {style}
FLOW TYPE: {flow_type}

OUTPUT STRUCTURE (MUST follow this exact order):
{schema_lines}

CRITICAL RULES:
- Reference the user's question directly at least once
- Prioritize the user's stated intent over broad textbook summary, especially for palm, Sun/Moon, daily, and lunar flows
- Reference available anchors from the list provided (prioritize primary anchors)
- Use anchors relevant to this flow type
- Ground interpretations in the provided reference material
- Include directional forecasts using anchor-backed language
- NO medical/legal/financial advice
- NO generic filler phrases
- Each section must feel specific to THIS person's data
- Keep interpretation deterministic in style: choose a dominant through-line and maintain it
- Avoid over-hedging; do not stack "maybe/perhaps/might" repeatedly
- Avoid technical or textbook language; keep it plain and human
- Use concrete, relatable phrasing with grit, determination, and momentum
- Total output: 600-900 words
- Output MUST include all delimiters for this flow exactly as specified
- After the main text of EACH section, include a deeper expansion starting with:
  DEEP_INSIGHT: <1-2 paragraphs with more detail and nuance>

TONE: Insightful, bold, grounded, and human. Real-world and memorable.

{self._voice_contract(short_form=False)}
{self._prediction_contract(short_form=False)}

Output ONLY the reading text in this format:

{format_lines}

{reference_block}"""

        # Build user message
        palm_section = ""
        if palm_facts:
            palm_section = f"\n\nPalm features:\n{json.dumps(palm_facts, indent=2)}"
        
        user_content = f"""Create a complete personalised reading:

User's Question: "{question}"

Primary anchors (must use these first):
{primary_anchors}

All anchors available:
{self._format_anchors(anchors)}

Astrology Data:
{json.dumps(astrology_facts, indent=2)}

Tarot Cards:
{json.dumps(tarot_cards, indent=2)}{palm_section}

Generate the full reading following this flow schema and the grounding rules."""

        system, messages = self._build_messages(system_prompt, user_content)
        
        try:
            # Call Bedrock Converse API
            response = self.client.converse(
                modelId=self.full_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": self.full_max_tokens,
                    "temperature": 0.78,
                    "topP": 0.92
                }
            )
            
            # Extract response
            output_text = response['output']['message']['content'][0]['text']
            
            # Parse sections
            sections = self._parse_sections_by_schema(output_text, schema)
            
            # Extract token usage
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            
            # Calculate cost
            cost = self._calculate_cost(self.full_model, input_tokens, output_tokens)
            
            return {
                'sections': sections,
                'full_text': output_text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost,
                'model': self.full_model
            }
            
        except Exception as e:
            raise RuntimeError(f"Bedrock full reading generation failed: {str(e)}")

    def generate_lunar_forecast(
        self,
        question: str,
        zodiac: Dict[str, str],
        year_label: str
    ) -> Dict[str, Any]:
        """
        Generate a Lunar New Year forecast section.
        """
        reference_block = self._build_reference_block()

        system_prompt = f"""You are an insightful metaphysical reader writing a Lunar New Year forecast add-on.

CRITICAL RULES:
- 2-3 paragraphs
- Grounded, opportunity-focused, with directional forecasting
- Include at least one concrete "expect / likely" forward-looking line
- Be specific to the user's zodiac animal + element
- Keep one clear year theme and build around it
- Avoid technical jargon and keep it human, direct, and relatable

{self._voice_contract(short_form=False)}
{self._prediction_contract(short_form=True)}

TONE: Grounded, practical, bold, with gentle grit.

{reference_block}"""

        user_content = f"""Write a Lunar New Year forecast add-on.

User question/intention: "{question}"
Chinese zodiac: {json.dumps(zodiac)}
Year label: {year_label}

Focus on themes, growth areas, energies to work with, and challenges to navigate."""

        system, messages = self._build_messages(system_prompt, user_content)

        try:
            response = self.client.converse(
                modelId=self.full_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": 450,
                    "temperature": 0.76,
                    "topP": 0.92
                }
            )

            output_text = response['output']['message']['content'][0]['text']
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            cost = self._calculate_cost(self.full_model, input_tokens, output_tokens)

            return {
                "text": output_text.strip(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "model": self.full_model
            }
        except Exception as e:
            raise RuntimeError(f"Bedrock lunar forecast generation failed: {str(e)}")

    def generate_compatibility_preview(
        self,
        person1: Dict[str, Any],
        person2: Dict[str, Any],
        synastry: Dict[str, Any],
        zodiac_compatibility: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate compatibility preview teaser using Nova Lite.
        """
        reference_block = self._build_reference_block()
        system_prompt = f"""You are an insightful metaphysical reader providing compatibility preview teasers.

CRITICAL RULES:
- Output ONLY 2-3 sentences (max 50 words)
- Ground interpretations in the provided reference material
- Include one concise forward-looking relationship call
- Keep one clear relationship pattern front-and-center
- Avoid technical or textbook language
- Must feel specific to THESE two people

TONE: Grounded, bold, intriguing, relatable.

{self._voice_contract(short_form=True)}
{self._prediction_contract(short_form=True)}

{reference_block}"""

        user_content = f"""Generate a compatibility preview teaser:

Person 1: {json.dumps(person1, indent=2)}
Person 2: {json.dumps(person2, indent=2)}
Synastry: {json.dumps(synastry, indent=2)}
Chinese zodiac harmony: {json.dumps(zodiac_compatibility, indent=2)}"""

        system, messages = self._build_messages(system_prompt, user_content)

        try:
            response = self.client.converse(
                modelId=self.preview_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": self.preview_max_tokens,
                    "temperature": 0.7,
                    "topP": 0.92
                }
            )
            output_text = response['output']['message']['content'][0]['text']
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            cost = self._calculate_cost(self.preview_model, input_tokens, output_tokens)

            return {
                "teaser_text": output_text.strip(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "model": self.preview_model
            }
        except Exception as e:
            raise RuntimeError(f"Bedrock compatibility preview failed: {str(e)}")

    def generate_compatibility_reading(
        self,
        person1: Dict[str, Any],
        person2: Dict[str, Any],
        synastry: Dict[str, Any],
        zodiac_compatibility: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a 6-section compatibility reading using Nova Pro.
        """
        reference_block = self._build_reference_block()
        system_prompt = f"""You are an insightful metaphysical reader creating a compatibility reading.

OUTPUT STRUCTURE (MUST follow this exact order):
1. opening (1 paragraph)
2. individual_essences (2 paragraphs - both people)
3. astrological_synastry (2 paragraphs)
4. zodiac_harmony (1-2 paragraphs)
5. shared_growth_edges (1-2 paragraphs)
6. guidance (1 paragraph)

CRITICAL RULES:
- Ground interpretations in the provided reference material
- Include directional relationship forecasts backed by synastry/zodiac anchors
- NO medical/legal/financial advice
- Keep a deterministic through-line: one core dynamic, then supporting layers
- Avoid technical or textbook language
- Must feel specific to THESE two people
- Total output: 500-800 words
- Output MUST include all 6 section delimiters exactly as specified

TONE: Grounded, candid, and memorable with grit.

{self._voice_contract(short_form=False)}
{self._prediction_contract(short_form=False)}

Output ONLY the reading text in this format:

---OPENING---
[text]

---INDIVIDUAL_ESSENCES---
[text]

---ASTROLOGICAL_SYNASTRY---
[text]

---ZODIAC_HARMONY---
[text]

---SHARED_GROWTH_EDGES---
[text]

---GUIDANCE---
[text]

{reference_block}"""

        user_content = f"""Create a compatibility reading.

Person 1: {json.dumps(person1, indent=2)}
Person 2: {json.dumps(person2, indent=2)}
Synastry: {json.dumps(synastry, indent=2)}
Chinese zodiac harmony: {json.dumps(zodiac_compatibility, indent=2)}"""

        system, messages = self._build_messages(system_prompt, user_content)

        try:
            response = self.client.converse(
                modelId=self.full_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": self.full_max_tokens,
                    "temperature": 0.78,
                    "topP": 0.92
                }
            )
            output_text = response['output']['message']['content'][0]['text']
            sections = self._parse_compatibility_sections(output_text)
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            cost = self._calculate_cost(self.full_model, input_tokens, output_tokens)

            return {
                "sections": sections,
                "full_text": output_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "model": self.full_model
            }
        except Exception as e:
            raise RuntimeError(f"Bedrock compatibility reading failed: {str(e)}")

    def generate_blessing(
        self,
        question: str,
        themes: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a short blessing using Nova Lite.
        """
        system_prompt = f"""You are writing a short blessing.

CRITICAL RULES:
- 2-3 sentences, concise and warm
- Grounded, hopeful, not religious
- Use "may" language, no predictions
- Avoid technical or clinical language
- Keep it human and real, not greeting-card generic

TONE: Warm, grounded, hopeful, with personality.

{self._voice_contract(short_form=True)}"""

        user_content = f"""Write a blessing based on this:

Question/intention: "{question}"
Themes: {json.dumps(themes)}"""

        system, messages = self._build_messages(system_prompt, user_content)

        try:
            response = self.client.converse(
                modelId=self.preview_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": 180,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            )
            output_text = response['output']['message']['content'][0]['text']
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            cost = self._calculate_cost(self.preview_model, input_tokens, output_tokens)

            return {
                "blessing_text": output_text.strip(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "model": self.preview_model
            }
        except Exception as e:
            raise RuntimeError(f"Bedrock blessing failed: {str(e)}")

    def generate_feng_shui_analysis(
        self,
        context: Dict[str, Any],
        vision_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Feng Shui analysis using Nova Pro.
        """
        system_prompt = f"""You are a Feng Shui consultant analyzing this space.

ANALYSIS FRAMEWORK:
1. Bagua map
2. Five elements balance
3. Energy flow (chi)
4. Recommendations
5. Priority actions
6. Overall guidance

CRITICAL RULES:
- Practical, grounded, no superstition
- 10-15 specific actionable recommendations
- Explain why each recommendation matters
- Avoid mystical guarantees
- Use plain, direct language a real person can act on today

VOICE:
{self._voice_contract(short_form=False)}

OUTPUT FORMAT:
---OVERVIEW---
[text]

---BAGUA_MAP---
[text]

---ENERGY_FLOW---
[text]

---RECOMMENDATIONS---
[text]

---PRIORITY_ACTIONS---
[text]

---GUIDANCE---
[text]
"""

        user_content = f"""Context: {json.dumps(context, indent=2)}

Vision analysis (JSON):
{json.dumps(vision_analysis, indent=2)}"""

        system, messages = self._build_messages(system_prompt, user_content)

        try:
            response = self.client.converse(
                modelId=self.full_model,
                messages=messages,
                system=[{"text": system}],
                inferenceConfig={
                    "maxTokens": self.full_max_tokens,
                    "temperature": 0.65,
                    "topP": 0.9
                }
            )
            output_text = response['output']['message']['content'][0]['text']
            sections = self._parse_feng_shui_sections(output_text)
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            cost = self._calculate_cost(self.full_model, input_tokens, output_tokens)

            return {
                "sections": sections,
                "full_text": output_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "model": self.full_model
            }
        except Exception as e:
            raise RuntimeError(f"Bedrock feng shui analysis failed: {str(e)}")
    
    def _parse_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Parse the delimited output into structured sections.
        
        Args:
            text: Raw output text with section delimiters
            
        Returns:
            List of section dicts with id and text
        """
        section_map = {
            'OPENING_INVOCATION': 'opening_invocation',
            'ASTROLOGICAL_FOUNDATION': 'astrological_foundation',
            'TAROT_NARRATIVE': 'tarot_narrative',
            'PALM_INSIGHT': 'palm_insight',
            'INTEGRATED_SYNTHESIS': 'integrated_synthesis',
            'REFLECTIVE_GUIDANCE': 'reflective_guidance',
            'CLOSING_PROMPT': 'closing_prompt'
        }
        
        sections = []
        current_section = None
        current_text = []
        
        for line in text.split('\n'):
            # Check if line is a delimiter
            for delimiter, section_id in section_map.items():
                if f"---{delimiter}---" in line:
                    # Save previous section if exists
                    if current_section:
                        raw_text = '\n'.join(current_text).strip()
                        deep_text = None
                        if "DEEP_INSIGHT:" in raw_text:
                            parts = raw_text.split("DEEP_INSIGHT:", 1)
                            raw_text = parts[0].strip()
                            deep_text = parts[1].strip()
                        section_payload = {
                            'id': current_section,
                            'text': raw_text
                        }
                        if deep_text:
                            section_payload['deep_text'] = deep_text
                        sections.append(section_payload)
                    # Start new section
                    current_section = section_id
                    current_text = []
                    break
            else:
                # Not a delimiter, add to current section
                if current_section:
                    current_text.append(line)
        
        # Save last section
        if current_section:
            raw_text = '\n'.join(current_text).strip()
            deep_text = None
            if "DEEP_INSIGHT:" in raw_text:
                parts = raw_text.split("DEEP_INSIGHT:", 1)
                raw_text = parts[0].strip()
                deep_text = parts[1].strip()
            section_payload = {
                'id': current_section,
                'text': raw_text
            }
            if deep_text:
                section_payload['deep_text'] = deep_text
            sections.append(section_payload)
        
        return sections

    def _parse_compatibility_sections(self, text: str) -> List[Dict[str, str]]:
        section_map = {
            'OPENING': 'opening',
            'INDIVIDUAL_ESSENCES': 'individual_essences',
            'ASTROLOGICAL_SYNASTRY': 'astrological_synastry',
            'ZODIAC_HARMONY': 'zodiac_harmony',
            'SHARED_GROWTH_EDGES': 'shared_growth_edges',
            'GUIDANCE': 'guidance'
        }

        sections = []
        current_section = None
        current_text = []

        for line in text.split('\n'):
            for delimiter, section_id in section_map.items():
                if f"---{delimiter}---" in line:
                    if current_section:
                        raw_text = '\n'.join(current_text).strip()
                        sections.append({'id': current_section, 'text': raw_text})
                    current_section = section_id
                    current_text = []
                    break
            else:
                if current_section:
                    current_text.append(line)

        if current_section:
            raw_text = '\n'.join(current_text).strip()
            sections.append({'id': current_section, 'text': raw_text})

        return sections

    def _parse_feng_shui_sections(self, text: str) -> List[Dict[str, str]]:
        section_map = {
            'OVERVIEW': 'overview',
            'BAGUA_MAP': 'bagua_map',
            'ENERGY_FLOW': 'energy_flow',
            'RECOMMENDATIONS': 'recommendations',
            'PRIORITY_ACTIONS': 'priority_actions',
            'GUIDANCE': 'guidance'
        }

        sections = []
        current_section = None
        current_text = []

        for line in text.split('\n'):
            for delimiter, section_id in section_map.items():
                if f"---{delimiter}---" in line:
                    if current_section:
                        raw_text = '\n'.join(current_text).strip()
                        sections.append({'id': current_section, 'text': raw_text})
                    current_section = section_id
                    current_text = []
                    break
            else:
                if current_section:
                    current_text.append(line)

        if current_section:
            raw_text = '\n'.join(current_text).strip()
            sections.append({'id': current_section, 'text': raw_text})

        return sections


# Singleton instance
_bedrock_service = None

def get_bedrock_service() -> BedrockService:
    """Get or create singleton Bedrock service instance."""
    global _bedrock_service
    if _bedrock_service is None:
        _bedrock_service = BedrockService()
    return _bedrock_service
