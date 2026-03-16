"""
Feng Shui vision analysis using Bedrock Nova Pro (multimodal).
"""

import os
from typing import List, Dict, Any
import boto3


class FengShuiVisionService:
    def __init__(self):
        region = os.getenv('AWS_REGION', 'us-east-1')
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = os.getenv('FENG_SHUI_VISION_MODEL', 'us.amazon.nova-pro-v1:0')

        self.costs = {
            'us.amazon.nova-pro-v1:0': {'input': 0.0008, 'output': 0.0032},
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        cost_per_1k = self.costs.get(self.model_id)
        if not cost_per_1k:
            return 0.0
        input_cost = (input_tokens / 1000) * cost_per_1k['input']
        output_cost = (output_tokens / 1000) * cost_per_1k['output']
        return round(input_cost + output_cost, 6)

    def analyze_images(
        self,
        images: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        images: list of {"format": "jpeg|png", "bytes": b"..."}
        context: {room_purpose, user_goals, compass_direction, analysis_type}
        """
        system_prompt = """You are a Feng Shui consultant analyzing a space.

Return JSON with:
- element_balance: list of detected elements and notes
- bagua_zones: observations about zones or missing areas
- flow_issues: blockages, sharp angles, circulation notes
- strengths: existing positives
- recommendations: 10-15 specific actions with short rationale
"""

        user_content = [
            {"text": f"Context: {context}"},
        ]
        for image in images:
            user_content.append({
                "image": {
                    "format": image["format"],
                    "source": {"bytes": image["bytes"]}
                }
            })

        response = self.client.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": user_content}],
            system=[{"text": system_prompt}],
            inferenceConfig={
                "maxTokens": 800,
                "temperature": 0.6,
                "topP": 0.9
            }
        )

        output_text = response['output']['message']['content'][0]['text']
        usage = response.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)
        cost = self._calculate_cost(input_tokens, output_tokens)

        return {
            "raw_text": output_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "model": self.model_id
        }


_feng_shui_vision_service = None


def get_feng_shui_vision_service() -> FengShuiVisionService:
    global _feng_shui_vision_service
    if _feng_shui_vision_service is None:
        _feng_shui_vision_service = FengShuiVisionService()
    return _feng_shui_vision_service
