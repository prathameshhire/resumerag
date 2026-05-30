from pathlib import Path


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


class ConversionError(Exception):
    pass


class MarkItDownService:
    def convert_file_to_markdown(self, file_path: Path) -> str:
        extension = file_path.suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ConversionError(f"Unsupported file type: {extension}")

        if extension in {".md", ".txt"}:
            return file_path.read_text(encoding="utf-8", errors="replace")

        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            raise ConversionError("MarkItDown is not installed in the backend environment.") from exc

        try:
            result = MarkItDown().convert(str(file_path))
        except Exception as exc:
            raise ConversionError("Document conversion failed.") from exc

        text_content = getattr(result, "text_content", None)
        if not isinstance(text_content, str):
            raise ConversionError("Document conversion returned no Markdown text.")

        return text_content
