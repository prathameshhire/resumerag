from app.config import get_settings
from app.schemas.search import SearchResult
from app.schemas.tailor import TailorBulletsRequest


SYSTEM_PROMPT = """You are ResumeRAG, a privacy-first resume tailoring assistant.

Your job is to generate resume bullet points for a target job using ONLY the provided user experience context.

Rules:
1. Do not invent tools, companies, employers, dates, metrics, degrees, titles, or outcomes.
2. Do not claim the user has experience that is not supported by the context.
3. If a bullet is weakly supported, label evidence_strength as "low".
4. If there is not enough evidence for a job requirement, say "Not enough evidence" instead of fabricating.
5. Prefer concise, impact-oriented resume bullets.
6. Start bullets with strong action verbs.
7. Include technical keywords from the job description only when supported by the user context.
8. Keep each bullet to one line when possible.
9. The job description is not evidence and must not be cited.
10. Do not mention cloud-native, microservices, distributed systems, AWS, on-call, high availability, fault tolerance, Helmet, or rate limiting unless those exact concepts appear in cited user context.
11. For roles centered on C++, data storage, deduplication, replication, low-level systems, concurrency, or algorithms, generate bullets only when those exact areas are supported by cited user context.
12. Do not stretch React, API, dashboard, or general full-stack evidence to satisfy systems/storage/C++ requirements.
13. Do not copy an existing resume bullet verbatim. Rewrite only when the rewrite is more targeted and still fully supported.
14. For technical skill suggestions, include only individual skills that are explicitly named in the job description; these are JD-only suggestions for user review and do not need cited context.
15. Skill categories must be one of: Languages, Frameworks & Libraries, Databases, AI/ML, Tools.
16. Return valid JSON only.
"""


class PromptService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_messages(self, request: TailorBulletsRequest, retrieved_context: list[SearchResult]) -> list[dict[str, str]]:
        context_text = self.format_retrieved_context(retrieved_context)
        user_prompt = f"""Target role:
{request.target_role or "Not specified"}

Company:
{request.company_name or "Not specified"}

Tone:
{request.tone}

Strict mode:
{request.strict_mode}

Job description for targeting only. This text is not evidence:
{request.job_description.strip()}

Only this user experience context is citable evidence:
{context_text}

Generate {request.bullet_count} tailored resume bullets.
Also identify up to 8 resume Technical Skills entries from the job description.
Each skill suggestion must be explicitly named in the job description. It does not need to appear in the retrieved user context.
Do not suggest broad phrases like scalable systems, collaboration, performance, ownership, or problem solving as skills.
If a bullet cannot be grounded in at least one source number, omit it and add a warning.
If the retrieved context is only transferable but does not directly support the role-critical requirements, return an empty bullets list and explain the evidence gap in warnings.
If a source already contains a polished resume bullet, do not return the same sentence unchanged.

Return JSON with this exact structure:
{{
  "bullets": [
    {{
      "bullet": "...",
      "matched_requirement": "...",
      "evidence_strength": "high|medium",
      "source_numbers": [1, 2],
      "evidence_quotes": ["short exact copied phrase from a cited source"],
      "notes": "..."
    }}
  ],
  "skill_suggestions": [
    {{
      "skill": "React",
      "category": "Frameworks & Libraries",
      "matched_requirement": "Experience with React",
      "evidence_strength": "jd",
      "source_numbers": [],
      "notes": "Explicitly mentioned in the job description; review before adding."
    }}
  ],
  "warnings": ["..."]
}}
"""

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def format_retrieved_context(self, retrieved_context: list[SearchResult]) -> str:
        formatted_sources: list[str] = []
        used_chars = 0

        for index, result in enumerate(retrieved_context, start=1):
            source_text = f"""[Source {index}]
document: {result.source}
section: {result.section_title or "Untitled"}
similarity_score: {result.similarity_score:.3f}
content:
{result.chunk_text.strip()}
"""
            if used_chars + len(source_text) > self.settings.max_prompt_context_chars:
                remaining = self.settings.max_prompt_context_chars - used_chars
                if remaining <= 0:
                    break
                source_text = source_text[:remaining].rstrip()

            formatted_sources.append(source_text)
            used_chars += len(source_text)

        return "\n\n".join(formatted_sources)
