"""Agent 1: Parser - Extracts structured specifications from research papers."""

import structlog
from typing import Dict, Any

from backend.agents.base import BaseAgent
from backend.models.state import AgentType
from backend.models.schemas import ParserOutput, PaperSpecification
from backend.services.gemini_client import gemini_client
from backend.services.pdf_processor import pdf_processor


logger = structlog.get_logger()


class ParserAgent(BaseAgent[Dict[str, Any], ParserOutput]):
    """Agent that parses research papers and extracts structured specifications."""

    def __init__(self):
        """Initialize Parser agent."""
        super().__init__(AgentType.PARSER)

    async def execute(
        self,
        input_data: Dict[str, Any],
        pipeline_id: str
    ) -> ParserOutput:
        """
        Parse research paper and extract structured specification.

        Args:
            input_data: Dict with 'paper_source' (PDF path or arXiv URL)
            pipeline_id: Pipeline identifier

        Returns:
            ParserOutput with extracted specification or error
        """
        paper_source = input_data.get("paper_source")

        if not paper_source:
            return ParserOutput(
                success=False,
                error="No paper source provided"
            )

        try:
            # Extract text from PDF
            self.logger.info("extracting_pdf", source=paper_source)
            paper_text = await pdf_processor.extract_text(paper_source)

            if not paper_text:
                return ParserOutput(
                    success=False,
                    error="Failed to extract text from PDF"
                )

            # Build parsing prompt
            prompt = self._build_parsing_prompt(paper_text)

            # Call Gemini for structured extraction
            self.logger.info("calling_gemini_for_parsing")
            specification = await gemini_client.generate_structured(
                prompt=prompt,
                response_schema=PaperSpecification,
                temperature=0.1  # Low temperature for accurate extraction
            )

            if not specification:
                return ParserOutput(
                    success=False,
                    error="Gemini failed to parse paper specification"
                )

            self.logger.info(
                "paper_parsed_successfully",
                title=specification.title,
                ambiguities_count=len(specification.ambiguities)
            )

            return ParserOutput(
                success=True,
                specification=specification,
                extraction_metadata={
                    "paper_length_chars": len(paper_text),
                    "ambiguities_detected": len(specification.ambiguities)
                }
            )

        except Exception as e:
            self.logger.error("parser_execution_error", error=str(e))
            return ParserOutput(
                success=False,
                error=f"Parser execution failed: {str(e)}"
            )

    def _build_parsing_prompt(self, paper_text: str) -> str:
        """Build the parsing prompt for Gemini."""
        return f"""You are a research paper parser for a reproducibility engine.

Extract a structured specification from the following research paper.

CRITICAL INSTRUCTIONS:
1. Extract ONLY information that is explicitly stated in the paper
2. For missing information, mark fields as "unspecified" or use empty lists
3. Identify ambiguities where implementation details are unclear
4. Do NOT hallucinate or invent values
5. Focus on technical details needed for implementation

PAPER TEXT:
{paper_text}

Extract:
- Title and authors
- Abstract
- Problem definition
- Architecture details (model structure, layers, components)
- Hyperparameters (learning rate, batch size, epochs, optimizer, etc.)
- Dataset information (name, preprocessing, train/val/test splits)
- Evaluation methodology
- Reported metrics and results
- Baselines and ablations
- Important equations
- Implementation ambiguities (missing details)

If a section is not present or unclear, explicitly mark it as such.
"""


# Global parser agent instance
parser_agent = ParserAgent()
