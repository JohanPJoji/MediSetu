from pathlib import Path


class OCRService:
    """Provider-agnostic document OCR abstraction.

    The local prototype supports UTF-8 text extraction only. Image/PDF OCR
    must be supplied through a configured external OCR provider.
    """

    async def extract_text(self, filename: str, content: bytes, content_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if content_type == "text/plain" or suffix in {".txt", ".csv", ".md"}:
            return content.decode("utf-8", errors="replace")
        raise RuntimeError(
            "OCR provider is not configured for binary documents. "
            "Configure OCR_PROVIDER/OCR_API_KEY for PDF/image processing."
        )


ocr_service = OCRService()
