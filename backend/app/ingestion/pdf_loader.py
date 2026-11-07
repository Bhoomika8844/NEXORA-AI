
import pymupdf
from pathlib import Path


def extract_text_from_pdf(pdf_path: str):
    """
    Extract text from a PDF while preserving page numbers.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of dictionaries containing page numbers and text.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    extracted_pages = []

    try:
        with pymupdf.open(pdf_path) as document:

            if document.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")

            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()

                if text:
                    extracted_pages.append({
                        "page_number": page_number,
                        "text": text
                    })

    except Exception as error:
        if isinstance(error, (ValueError, FileNotFoundError)):
            raise
        raise ValueError(f"Could not read PDF: {error}") from error

    if not extracted_pages:
        raise ValueError(
            "No extractable text found. The PDF may be empty or scanned."
        )

    return extracted_pages
