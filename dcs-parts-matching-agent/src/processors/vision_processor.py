"""
Vision-based document processor for technical drawings and images.

Uses AI vision models (GPT-4 Vision, Claude 3) to analyze technical drawings,
schematics, and photographs of parts.
"""

import base64
import json
from pathlib import Path
from typing import Optional, Dict, Any
import re

from ..core.models import (
    ExtractedFeatures, DocumentType, Specification,
    SpecificationType, DimensionalData
)
from ..core.config import get_settings
from ..utils.logger import get_logger
from .base_processor import BaseDocumentProcessor

logger = get_logger(__name__)


class VisionProcessor(BaseDocumentProcessor):
    """Process images and technical drawings using AI vision models."""

    def __init__(self):
        """Initialize vision processor."""
        super().__init__()
        self.supported_types = [DocumentType.IMAGE, DocumentType.PDF]
        self.settings = get_settings()

    async def process(self, file_path: Path, additional_context: Optional[str] = None) -> ExtractedFeatures:
        """
        Process image/drawing using vision AI.

        Args:
            file_path: Path to image file
            additional_context: Optional context about the part

        Returns:
            ExtractedFeatures with specifications and dimensions
        """
        logger.info(f"Processing image with vision AI: {file_path}")

        # Encode image to base64
        image_data = self._encode_image(file_path)

        # Analyze with vision model
        analysis = await self._analyze_with_vision_model(image_data, additional_context)

        # Parse analysis into structured features
        features = self._parse_vision_analysis(analysis)

        return await self.postprocess(features)

    def _encode_image(self, file_path: Path) -> str:
        """
        Encode image to base64.

        Args:
            file_path: Path to image

        Returns:
            Base64 encoded image string
        """
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def _analyze_with_vision_model(
        self,
        image_data: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze image using vision AI model.

        Args:
            image_data: Base64 encoded image
            additional_context: Additional context

        Returns:
            Analysis results as dict
        """
        prompt = self._build_vision_prompt(additional_context)

        # Use OpenAI GPT-4 Vision or Claude 3
        if self.settings.use_vision_model.startswith("gpt"):
            return await self._analyze_with_openai(image_data, prompt)
        elif self.settings.use_vision_model.startswith("claude"):
            return await self._analyze_with_claude(image_data, prompt)
        else:
            raise ValueError(f"Unsupported vision model: {self.settings.use_vision_model}")

    def _build_vision_prompt(self, additional_context: Optional[str] = None) -> str:
        """
        Build prompt for vision model.

        Args:
            additional_context: Additional context

        Returns:
            Formatted prompt string
        """
        prompt = """Analyze this technical drawing or part image and extract the following information in JSON format:

{
  "part_type": "Description of what this part is",
  "specifications": [
    {
      "spec_type": "voltage_rating|current_rating|pressure_rating|temperature_range|dimension|connection_type|mounting_type|material|protocol|io_count|power_consumption|other",
      "name": "Specification name",
      "value": "Value",
      "unit": "Unit if applicable",
      "is_critical": true/false
    }
  ],
  "dimensions": {
    "width": number or null,
    "height": number or null,
    "depth": number or null,
    "diameter": number or null,
    "unit": "mm|inches|cm",
    "additional_dimensions": {}
  },
  "visible_text": "Any text visible in the image",
  "part_numbers": ["Any part numbers found"],
  "visual_features": {
    "connector_types": [],
    "mounting_type": "",
    "housing_material": "",
    "notable_features": []
  },
  "overall_description": "Detailed description of the part"
}

Focus on:
1. Critical specifications like voltage, current, pressure ratings
2. Physical dimensions with units
3. Connection/mounting types
4. Any visible part numbers or text
5. Material and construction details
"""

        if additional_context:
            prompt += f"\n\nAdditional context: {additional_context}"

        prompt += "\n\nProvide ONLY the JSON output, no additional text."

        return prompt

    async def _analyze_with_openai(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze with OpenAI GPT-4 Vision.

        Args:
            image_data: Base64 encoded image
            prompt: Analysis prompt

        Returns:
            Analysis results
        """
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.settings.openai_api_key)

            response = await client.chat.completions.create(
                model=self.settings.use_vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature
            )

            content = response.choices[0].message.content
            return self._parse_json_response(content)

        except Exception as e:
            logger.error(f"OpenAI vision analysis failed: {e}")
            raise

    async def _analyze_with_claude(self, image_data: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze with Anthropic Claude 3.

        Args:
            image_data: Base64 encoded image
            prompt: Analysis prompt

        Returns:
            Analysis results
        """
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)

            message = await client.messages.create(
                model=self.settings.use_vision_model,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            content = message.content[0].text
            return self._parse_json_response(content)

        except Exception as e:
            logger.error(f"Claude vision analysis failed: {e}")
            raise

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from model response.

        Args:
            content: Model response text

        Returns:
            Parsed JSON dict
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from response")

        # Return empty structure if parsing fails
        return {
            "part_type": "",
            "specifications": [],
            "dimensions": {},
            "visible_text": content,
            "part_numbers": [],
            "visual_features": {},
            "overall_description": content
        }

    def _parse_vision_analysis(self, analysis: Dict[str, Any]) -> ExtractedFeatures:
        """
        Parse vision analysis into ExtractedFeatures.

        Args:
            analysis: Raw analysis dict

        Returns:
            ExtractedFeatures object
        """
        specifications = []
        for spec_data in analysis.get("specifications", []):
            try:
                spec = Specification(
                    spec_type=SpecificationType(spec_data.get("spec_type", "other")),
                    name=spec_data.get("name", ""),
                    value=str(spec_data.get("value", "")),
                    unit=spec_data.get("unit"),
                    is_critical=spec_data.get("is_critical", False),
                    confidence=0.8  # Vision extraction confidence
                )
                specifications.append(spec)
            except Exception as e:
                logger.warning(f"Failed to parse specification: {e}")

        # Parse dimensions
        dimensions = None
        dim_data = analysis.get("dimensions", {})
        if dim_data:
            try:
                dimensions = DimensionalData(
                    width=dim_data.get("width"),
                    height=dim_data.get("height"),
                    depth=dim_data.get("depth"),
                    diameter=dim_data.get("diameter"),
                    unit=dim_data.get("unit", "mm"),
                    additional_dimensions=dim_data.get("additional_dimensions", {})
                )
            except Exception as e:
                logger.warning(f"Failed to parse dimensions: {e}")

        return ExtractedFeatures(
            specifications=specifications,
            dimensions=dimensions,
            text_description=analysis.get("overall_description", ""),
            detected_part_numbers=analysis.get("part_numbers", []),
            visual_features=analysis.get("visual_features", {}),
            raw_ocr_text=analysis.get("visible_text", ""),
            extraction_metadata={
                "processor": "vision",
                "model": self.settings.use_vision_model,
                "part_type": analysis.get("part_type", "")
            }
        )
