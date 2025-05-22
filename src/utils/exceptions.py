
class PaperExtractorError(Exception):
    """Base exception for the paper metadata extractor."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class TextExtractionError(PaperExtractorError):
    """Raised when text extraction from PDF (or via OCR) fails."""
    pass

class DOIParsingError(PaperExtractorError):
    """Raised when DOI/ISSN cannot be parsed or is malformed."""
    pass

class TitleAuthorParsingError(PaperExtractorError):
    """Raised when title or author parsing heuristics fail."""
    pass

class SummarizationError(PaperExtractorError):
    """Raised when the LLM summarization API call fails or times out."""
    pass

class DatabaseError(PaperExtractorError):
    """Raised when any database insert/query fails."""
    pass

class FileSaveError(PaperExtractorError):
    """Raised when saving or loading files (PDF, Excel, logs) fails."""
    pass

class OCRExtractionError(Exception):
    """Raised when OCR fails for any page."""
    pass