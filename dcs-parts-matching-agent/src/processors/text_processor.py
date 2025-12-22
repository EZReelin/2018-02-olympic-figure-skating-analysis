"""
Text description processor.

Handles plain text descriptions of required parts using NLP and LLM analysis.
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

from ..core.models import ExtractedFeatures, DocumentType, Specification, SpecificationType
from ..core.config import get_settings
from ..utils.logger import get_logger
from .base_processor import BaseDocumentProcessor

logger = get_logger(__name__)


class TextProcessor(BaseDocumentProcessor):
    """Process text descriptions using NLP and LLM."""

    def __init__(self):
        """Initialize text processor."""
        super().__init__()
        self.supported_types = [DocumentType.TEXT]
        self.settings = get_settings()

    async def process(self, file_path: Path, additional_context: Optional[str] = None) -> ExtractedFeatures:
        """
        Process text description.

        Args:
            file_path: Path to text file (or can be text content directly)
            additional_context: Optional context

        Returns:
            ExtractedFeatures extracted from text
        """
        # Read text content
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        else:
            # If file doesn't exist, treat path as text content
            text_content = str(file_path)

        logger.info(f"Processing text description ({len(text_content)} characters)")

        # Use LLM to extract structured information
        analysis = await self._analyze_with_llm(text_content, additional_context)

        # Parse into ExtractedFeatures
        features = self._parse_llm_analysis(analysis, text_content)

        return await self.postprocess(features)

    async def _analyze_with_llm(
        self,
        text: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze text using LLM.

        Args:
            text: Text description
            additional_context: Optional context

        Returns:
            Structured analysis
        """
        prompt = self._build_analysis_prompt(text, additional_context)

        # Use OpenAI or Anthropic
        if self.settings.openai_api_key:
            return await self._analyze_with_openai(prompt)
        elif self.settings.anthropic_api_key:
            return await self._analyze_with_claude(prompt)
        else:
            # Fallback to basic regex extraction
            return self._basic_extraction(text)

    def _build_analysis_prompt(self, text: str, additional_context: Optional[str] = None) -> str:
        """
        Build prompt for LLM analysis.

        Args:
            text: Input text
            additional_context: Additional context

        Returns:
            Formatted prompt
        """
        prompt = f"""Extract technical specifications from this part description and return ONLY a JSON object:

Description: {text}

{f"Additional context: {additional_context}" if additional_context else ""}

Return JSON in this exact format:
{{
  "part_type": "What type of DCS/industrial part this is",
  "specifications": [
    {{
      "spec_type": "voltage_rating|current_rating|pressure_rating|temperature_range|dimension|connection_type|mounting_type|material|protocol|io_count|power_consumption|other",
      "name": "Specification name",
      "value": "Value",
      "unit": "Unit if applicable",
      "is_critical": true/false
    }}
  ],
  "inferred_requirements": [
    "Any requirements or constraints inferred from the description"
  ],
  "keywords": ["Key technical terms"],
  "summary": "Brief summary of requirements"
}}

Extract:
- Voltage, current, pressure, temperature ratings
- Dimensions and physical specifications
- Connection types (RS-485, Ethernet, etc.)
- I/O counts (digital inputs, analog outputs, etc.)
- Protocols (Modbus, Profibus, etc.)
- Environmental requirements
- Mounting specifications

Return ONLY the JSON, no other text."""

        return prompt

    async def _analyze_with_openai(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze with OpenAI.

        Args:
            prompt: Analysis prompt

        Returns:
            Parsed response
        """
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.settings.openai_api_key)

            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a technical specification extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.settings.temperature,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._basic_extraction(prompt)

    async def _analyze_with_claude(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze with Claude.

        Args:
            prompt: Analysis prompt

        Returns:
            Parsed response
        """
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)

            message = await client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=self.settings.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = message.content[0].text

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return self._basic_extraction(prompt)

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return self._basic_extraction(prompt)

    def _basic_extraction(self, text: str) -> Dict[str, Any]:
        """
        Basic regex-based extraction fallback.

        Args:
            text: Input text

        Returns:
            Basic extraction results
        """
        specifications = []

        # Extract voltage
        voltage_matches = re.findall(r'(\d+\.?\d*)\s*(?:V|volt|VDC|VAC)', text, re.IGNORECASE)
        for match in voltage_matches[:2]:  # Limit to first 2
            specifications.append({
                "spec_type": "voltage_rating",
                "name": "Voltage",
                "value": match,
                "unit": "V",
                "is_critical": True
            })

        # Extract current
        current_matches = re.findall(r'(\d+\.?\d*)\s*(?:A|amp|mA)', text, re.IGNORECASE)
        for match in current_matches[:2]:
            specifications.append({
                "spec_type": "current_rating",
                "name": "Current",
                "value": match,
                "unit": "A",
                "is_critical": True
            })

        # Extract I/O counts
        io_matches = re.findall(r'(\d+)\s*(?:digital|analog)?\s*(?:input|output|I/O)', text, re.IGNORECASE)
        for match in io_matches:
            specifications.append({
                "spec_type": "io_count",
                "name": "I/O Count",
                "value": match,
                "unit": None,
                "is_critical": False
            })

        return {
            "part_type": "Industrial Control Component",
            "specifications": specifications,
            "inferred_requirements": [],
            "keywords": [],
            "summary": text[:200]
        }

    def _parse_llm_analysis(self, analysis: Dict[str, Any], original_text: str) -> ExtractedFeatures:
        """
        Parse LLM analysis into ExtractedFeatures.

        Args:
            analysis: LLM analysis dict
            original_text: Original input text

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
                    confidence=0.85  # LLM extraction confidence
                )
                specifications.append(spec)
            except Exception as e:
                logger.warning(f"Failed to parse specification: {e}")

        return ExtractedFeatures(
            specifications=specifications,
            text_description=analysis.get("summary", original_text[:500]),
            raw_ocr_text=original_text,
            extraction_metadata={
                "processor": "text",
                "part_type": analysis.get("part_type", ""),
                "keywords": analysis.get("keywords", []),
                "inferred_requirements": analysis.get("inferred_requirements", [])
            }
        )
