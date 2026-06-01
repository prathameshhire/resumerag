from pydantic import BaseModel, Field


class LatexPdfRequest(BaseModel):
    latex: str = Field(..., min_length=1, max_length=500_000)
    filename: str = Field(default="resume.pdf", max_length=120)
