import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class LatexExportError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LatexService:
    def __init__(self, compiler: str = "pdflatex", timeout_seconds: int = 45) -> None:
        self.compiler = compiler
        self.timeout_seconds = timeout_seconds

    def compile_pdf(self, latex: str) -> bytes:
        compiler_path = shutil.which(self.compiler)
        if not compiler_path:
            raise LatexExportError(
                "PDF export requires pdflatex in the backend container. Rebuild the backend image so the LaTeX packages are installed.",
                status_code=503,
            )

        with tempfile.TemporaryDirectory(prefix="resumerag-latex-") as temp_dir:
            workdir = Path(temp_dir)
            source_path = workdir / "main.tex"
            pdf_path = workdir / "main.pdf"
            source_path.write_text(latex, encoding="utf-8")

            for _ in range(2):
                result = self._run_compiler(compiler_path, workdir)
                if result.returncode != 0:
                    raise LatexExportError(
                        f"LaTeX compilation failed:\n{self._trim_compiler_output(result.stdout, result.stderr, temp_dir)}",
                        status_code=422,
                    )

            if not pdf_path.exists():
                raise LatexExportError("LaTeX compilation completed, but no PDF was produced.", status_code=422)

            return pdf_path.read_bytes()

    def _run_compiler(self, compiler_path: str, workdir: Path) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "TEXMFOUTPUT": str(workdir),
            "openin_any": "p",
            "openout_any": "p",
        }

        try:
            return subprocess.run(
                [
                    compiler_path,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    "-no-shell-escape",
                    "main.tex",
                ],
                cwd=workdir,
                capture_output=True,
                env=env,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise LatexExportError(
                "LaTeX compilation timed out. Check for missing packages, runaway macros, or a very large resume source.",
                status_code=504,
            ) from exc

    @staticmethod
    def _trim_compiler_output(stdout: str, stderr: str, temp_dir: str) -> str:
        output = "\n".join(part for part in [stdout, stderr] if part).replace(temp_dir, "<temp>")
        output = output.strip()
        if not output:
            return "No compiler output was captured."
        return output[-4_000:]

    @staticmethod
    def safe_pdf_filename(filename: str | None) -> str:
        clean = re.sub(r"[^A-Za-z0-9._-]+", "-", filename or "resume.pdf").strip(".-")
        if not clean:
            clean = "resume.pdf"
        if clean.lower().endswith(".tex"):
            clean = clean[:-4]
        if not clean.lower().endswith(".pdf"):
            clean = f"{clean}.pdf"
        return clean
