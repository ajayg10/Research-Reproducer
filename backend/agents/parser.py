"""Agent 1: Parser - Extracts structured specifications from research papers."""

import structlog
from typing import Dict, Any

from backend.agents.base import BaseAgent
from backend.models.state import AgentType
from backend.models.schemas import ParserOutput, PaperSpecification
from backend.services.gemini_client import gemini_client
from backend.services.pdf_processor import pdf_processor
import google.generativeai as genai
import asyncio
from pathlib import Path


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
            gemini_file = None
            paper_text = ""
            files = None
            
            if Path(paper_source).exists():
                # Upload directly to Gemini for native parsing
                self.logger.info("uploading_pdf", source=paper_source)
                loop = asyncio.get_event_loop()
                gemini_file = await loop.run_in_executor(
                    None, lambda: genai.upload_file(path=paper_source)
                )
                files = [gemini_file]
                prompt = self._build_parsing_prompt("")
            else:
                # Fallback to pdf processor (e.g. if we download it in processor, though processor currently assumes local)
                self.logger.info("extracting_pdf", source=paper_source)
                paper_text = await pdf_processor.extract_text(paper_source)

                if not paper_text:
                    return ParserOutput(
                        success=False,
                        error="Failed to extract text from PDF and file does not exist locally"
                    )

                # Build parsing prompt
                prompt = self._build_parsing_prompt(paper_text)

            # Call Gemini for structured extraction
            self.logger.info("calling_gemini_for_parsing")
            specification = await gemini_client.generate_structured(
                prompt=prompt,
                response_schema=PaperSpecification,
                temperature=0.1,  # Low temperature for accurate extraction
                files=files
            )

            # Cleanup uploaded file
            if gemini_file:
                try:
                    await loop.run_in_executor(None, lambda: genai.delete_file(gemini_file.name))
                except Exception as cleanup_err:
                    self.logger.warning("failed_to_delete_gemini_file", error=str(cleanup_err))

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
                    "paper_length_chars": len(paper_text) if paper_text else 0,
                    "ambiguities_detected": len(specification.ambiguities),
                    "parsed_via_file_api": bool(gemini_file)
                }
            )

        except Exception as e:
            self.logger.error("parser_execution_error", error=str(e))
            if 'gemini_file' in locals() and gemini_file:
                try:
                    genai.delete_file(gemini_file.name)
                except:
                    pass
            return ParserOutput(
                success=False,
                error=f"Parser execution failed: {str(e)}"
            )

    def _build_parsing_prompt(self, paper_text: str = "") -> str:
        """Build the parsing prompt for Gemini."""
        base_prompt = """You are a research paper parser for a reproducibility engine.

Extract a structured specification from the following research paper.

CRITICAL INSTRUCTIONS:
1. Extract ONLY information that is explicitly stated in the paper
2. For missing information, mark fields as "unspecified" or use empty lists
3. Identify ambiguities where implementation details are unclear
4. Do NOT hallucinate or invent values
5. Focus on technical details needed for implementation

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
        if paper_text:
            return f"{base_prompt}\n\nPAPER TEXT:\n{paper_text}"
        return base_prompt


# Global parser agent instance
parser_agent = ParserAgent()
