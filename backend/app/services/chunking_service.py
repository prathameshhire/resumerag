from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class TextChunk:
    chunk_text: str
    section_title: str | None
    token_estimate: int
    metadata: dict[str, str] = field(default_factory=dict)


class ChunkingService:
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+?)\s*$")

    def __init__(self, chunk_size_chars: int, chunk_overlap_chars: int) -> None:
        self.chunk_size_chars = chunk_size_chars
        self.chunk_overlap_chars = min(chunk_overlap_chars, max(0, chunk_size_chars // 2))

    def chunk_markdown(self, markdown_text: str) -> list[TextChunk]:
        sections = self._split_sections(markdown_text)
        chunks: list[TextChunk] = []

        for section_title, section_text in sections:
            for chunk_text in self._chunk_section(section_text):
                cleaned = chunk_text.strip()
                if cleaned:
                    chunks.append(
                        TextChunk(
                            chunk_text=cleaned,
                            section_title=section_title,
                            token_estimate=max(1, len(cleaned) // 4),
                            metadata={"section_title": section_title} if section_title else {},
                        )
                    )

        return chunks

    def _split_sections(self, markdown_text: str) -> list[tuple[str | None, str]]:
        sections: list[tuple[str | None, str]] = []
        current_title: str | None = None
        current_lines: list[str] = []

        for line in markdown_text.splitlines():
            match = self.heading_pattern.match(line)
            if match:
                self._append_section(sections, current_title, current_lines)
                current_title = match.group(2).strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        self._append_section(sections, current_title, current_lines)
        return sections

    def _append_section(
        self,
        sections: list[tuple[str | None, str]],
        section_title: str | None,
        lines: list[str],
    ) -> None:
        section_text = "\n".join(lines).strip()
        if section_text:
            sections.append((section_title, section_text))

    def _chunk_section(self, section_text: str) -> list[str]:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", section_text) if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size_chars:
                text_to_split = f"{current}\n\n{paragraph}".strip() if current else paragraph
                chunks.extend(self._split_long_text(text_to_split))
                current = ""
                continue

            candidate = paragraph if not current else f"{current}\n\n{paragraph}"
            if len(candidate) <= self.chunk_size_chars:
                current = candidate
                continue

            chunks.append(current)
            overlap = self._overlap_text(current)
            current = f"{overlap}\n\n{paragraph}".strip() if overlap else paragraph

        if current:
            chunks.append(current)

        return chunks

    def _split_long_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        step = max(1, self.chunk_size_chars - self.chunk_overlap_chars)

        while start < len(text):
            end = min(len(text), start + self.chunk_size_chars)
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += step

        return chunks

    def _overlap_text(self, text: str) -> str:
        if self.chunk_overlap_chars <= 0 or len(text) <= self.chunk_overlap_chars:
            return ""
        return text[-self.chunk_overlap_chars :]
