"""PDF processing utilities."""

import structlog
from pathlib import Path
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


logger = structlog.get_logger()


class PDFProcessor:
    """Extract text from PDF files."""

    def __init__(self):
        """Initialize PDF processor."""
        if not PyPDF2 and not pdfplumber:
            logger.error("no_pdf_library_available")
            raise ImportError("Neither PyPDF2 nor pdfplumber is installed")

    async def extract_text(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text or None on failure
        """
        try:
            file_path = Path(pdf_path)

            if not file_path.exists():
                logger.error("pdf_file_not_found", path=pdf_path)
                return None

            logger.info("extracting_pdf_text", path=pdf_path)

            # Try pdfplumber first (better quality)
            if pdfplumber:
                return await self._extract_with_pdfplumber(file_path)

            # Fallback to PyPDF2
            return await self._extract_with_pypdf2(file_path)

        except Exception as e:
            logger.error("pdf_extraction_error", path=pdf_path, error=str(e))
            return None

    async def _extract_with_pdfplumber(self, file_path: Path) -> str:
        """Extract using pdfplumber."""
        text_parts = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num} ---\n{text}")

        full_text = "\n\n".join(text_parts)
        logger.info("pdf_extracted", pages=len(text_parts), chars=len(full_text))
        return full_text

    async def _extract_with_pypdf2(self, file_path: Path) -> str:
        """Extract using PyPDF2."""
        text_parts = []

        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        full_text = "\n\n".join(text_parts)
        logger.info("pdf_extracted", pages=len(text_parts), chars=len(full_text))
        return full_text


# Global PDF processor instance
pdf_processor = PDFProcessor()
