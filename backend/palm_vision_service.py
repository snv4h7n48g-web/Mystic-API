"""
Palm reading analysis using Claude 3.5 Sonnet Vision on AWS Bedrock.
Analyzes palm images and extracts features for reading generation.
"""

import boto3
import base64
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class PalmVisionService:
    """Service for analyzing palm images using Claude Vision."""
    
    def __init__(self):
        """Initialize Bedrock client for Claude Vision."""
        # Get credentials from environment
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Build client kwargs
        client_kwargs = {
            'service_name': 'bedrock-runtime',
            'region_name': region
        }
        
        # Only add explicit credentials if they're set
        if aws_access_key and aws_access_key != 'your_access_key_here':
            client_kwargs['aws_access_key_id'] = aws_access_key
            client_kwargs['aws_secret_access_key'] = aws_secret_key
        
        self.client = boto3.client(**client_kwargs)
        
        # Vision-capable model (override via env for account availability / inference profile)
        self.model_id = os.getenv(
            "PALM_VISION_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        
        # Cost tracking (approximate USD per 1000 tokens)
        self.cost_per_1k_input = 0.003
        self.cost_per_1k_output = 0.015
    
    def analyze_palm(
        self,
        image_data: bytes,
        handedness: str,
        is_dominant: bool
    ) -> Dict[str, Any]:
        """
        Analyze a palm image and extract features.
        
        Args:
            image_data: Raw image bytes (JPEG/PNG)
            handedness: "left" or "right"
            is_dominant: True if this is the dominant hand
            
        Returns:
            Dict with palm features, tokens, and cost
        """
        image_format = self._detect_image_format(image_data)
        
        # Build prompt for palm analysis
        analysis_prompt = self._build_palm_prompt(handedness, is_dominant)
        
        # Construct message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": image_format,
                            "source": {
                                "bytes": image_data
                            }
                        }
                    },
                    {
                        "text": analysis_prompt
                    }
                ]
            }
        ]
        
        try:
            # Call Bedrock with Claude Vision
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0.5,  # Lower temp for more consistent analysis
                    "topP": 0.9
                }
            )
            
            # Extract response
            output_text = response['output']['message']['content'][0]['text']
            
            # Parse JSON response
            palm_features = self._parse_palm_response(output_text)
            
            # Extract token usage
            usage = response.get('usage', {})
            input_tokens = usage.get('inputTokens', 0)
            output_tokens = usage.get('outputTokens', 0)
            
            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            return {
                'features': palm_features,
                'handedness': handedness,
                'is_dominant': is_dominant,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost_usd': cost,
                'model': self.model_id
            }
            
        except Exception as e:
            raise RuntimeError(f"Palm analysis failed: {str(e)}")
    
    def _build_palm_prompt(self, handedness: str, is_dominant: bool) -> str:
        """Build the analysis prompt for Claude Vision."""
        hand_desc = "dominant" if is_dominant else "non-dominant"
        
        return f"""Analyze this palm image ({handedness} hand, {hand_desc}).

Identify and describe the following features in detail:

1. **Major Lines:**
   - Life line: length, depth, clarity, any breaks or chains
   - Heart line: shape (curved/straight), position, depth
   - Head line: angle, length, any forks or islands
   - Fate line: presence, clarity (if visible)

2. **Mounts (flesh pads):**
   - Venus mount: prominence (high/medium/low)
   - Jupiter mount: development
   - Saturn mount: prominence
   - Apollo mount: visibility
   - Mercury mount: size
   - Luna mount: fullness

3. **Hand Shape:**
   - Overall shape: earth/air/fire/water type
   - Finger length relative to palm
   - Flexibility: rigid/flexible

4. **Notable Features:**
   - Any unusual markings
   - Stars, crosses, or triangles
   - Vertical lines
   - Overall clarity of lines

Return ONLY a JSON object with this exact structure:
{{
  "life_line": {{
    "length": "long/medium/short",
    "depth": "deep/medium/shallow",
    "quality": "clear/broken/chained",
    "description": "brief description"
  }},
  "heart_line": {{
    "shape": "curved/straight/mixed",
    "position": "high/medium/low",
    "depth": "deep/medium/shallow",
    "description": "brief description"
  }},
  "head_line": {{
    "angle": "horizontal/sloping/steep",
    "length": "long/medium/short",
    "quality": "clear/forked/island",
    "description": "brief description"
  }},
  "fate_line": {{
    "present": true/false,
    "clarity": "clear/faint/broken",
    "description": "brief description"
  }},
  "mounts": {{
    "venus": "prominent/moderate/flat",
    "jupiter": "developed/moderate/underdeveloped",
    "saturn": "prominent/moderate/flat",
    "apollo": "visible/moderate/minimal",
    "mercury": "large/medium/small",
    "luna": "full/moderate/flat"
  }},
  "hand_shape": {{
    "type": "earth/air/fire/water",
    "finger_length": "long/medium/short",
    "flexibility": "rigid/moderate/flexible"
  }},
  "overall_impression": "2-3 sentence summary of key features"
}}

        Be objective and descriptive. Focus on observable features."""

    def _detect_image_format(self, image_data: bytes) -> str:
        """Best-effort detection of image format for Bedrock."""
        if image_data.startswith(b"\x89PNG"):
            return "png"
        return "jpeg"
    
    def _parse_palm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the JSON response from Claude."""
        try:
            # Remove markdown code fences if present
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.startswith('```'):
                clean_text = clean_text[3:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            
            clean_text = clean_text.strip()
            
            # Parse JSON
            features = json.loads(clean_text)
            return features
            
        except json.JSONDecodeError as e:
            # If parsing fails, return a structured error
            return {
                "error": "Failed to parse palm analysis",
                "raw_response": response_text,
                "parse_error": str(e)
            }
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for the analysis."""
        input_cost = (input_tokens / 1000) * self.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.cost_per_1k_output
        return round(input_cost + output_cost, 6)


# Singleton instance
_palm_vision_service = None

def get_palm_vision_service() -> PalmVisionService:
    """Get or create singleton palm vision service."""
    global _palm_vision_service
    if _palm_vision_service is None:
        _palm_vision_service = PalmVisionService()
    return _palm_vision_service
