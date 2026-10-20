from src.agents.readme_extraction import ReadmeExtract
from src.llm import LLMService
from src.schemas.report_schema import RepoAnalysis, RepoComparisonReport
from src.schemas.repository_shema import RepoInput


def _format_repository(repo: RepoInput, readme: ReadmeExtract | None) -> str:
    readme_text = readme.to_prompt_text() if readme else "(No README available)"
    return (
        f"## Repository: {repo.full_name}\n"
        f"Description: {repo.description or '(none)'}\n"
        f"Stars: {repo.stargazers_count}\n"
        f"URL: {repo.html_url}\n\n"
        f"README:\n{readme_text}"
    )


async def generate_report(
    repositories: list[tuple[RepoInput, ReadmeExtract | None]],
) -> RepoComparisonReport:
    """Summarise each repository from its README and compare them against each other."""
    system = (
        "You are a software analyst helping a developer choose between GitHub repositories. "
        "You will be given the metadata and an extract of the README of each repository. "
        "For each repository, summarise what it does, its key features, tech stack, use cases, "
        "strengths and limitations. Then compare the repositories on the 3 to 6 criteria that "
        "matter most for choosing between them, and finish with a recommendation. "
        "Base everything on the provided content only; when information is missing, say so in "
        "the limitations instead of guessing. Refer to repositories by their exact full name. "
        "If there is only one repository, return an empty comparison list, and make the "
        "recommendation about who should use it and when."
    )
    content = "\n\n---\n\n".join(_format_repository(repo, readme) for repo, readme in repositories)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]

    llm = LLMService.active_llm().with_structured_output(RepoComparisonReport)
    return await llm.ainvoke(messages)


def _render_list(title: str, items: list[str]) -> str:
    if not items:
        return ""
    bullets = "\n".join(f"- {item}" for item in items)
    return f"**{title}**\n\n{bullets}"


def _render_analysis(analysis: RepoAnalysis, heading: str) -> str:
    parts = [
        f"{heading} {analysis.full_name}",
        analysis.summary,
        _render_list("Key features", analysis.key_features),
        f"**Tech stack:** {', '.join(analysis.tech_stack)}" if analysis.tech_stack else "",
        _render_list("Use cases", analysis.use_cases),
        _render_list("Strengths", analysis.strengths),
        _render_list("Limitations", analysis.limitations),
    ]
    return "\n\n".join(part for part in parts if part)


def render_report_markdown(report: RepoComparisonReport) -> str:
    """Render the report as markdown (headings and lists only, no tables)."""
    is_comparison = len(report.repositories) > 1
    parts = [f"## Overview\n\n{report.overview}"] if is_comparison else []
    parts += [
        _render_analysis(analysis, "###" if is_comparison else "##")
        for analysis in report.repositories
    ]
    if report.comparison:
        parts.append("## Comparison")
        for criterion in report.comparison:
            assessments = "\n".join(
                f"- **{item.full_name}:** {item.assessment}" for item in criterion.assessments
            )
            parts.append(
                f"### {criterion.criterion}\n\n{assessments}\n\nBest fit: **{criterion.best_fit}**"
            )
    parts.append(f"## Recommendation\n\n{report.recommendation}")
    return "\n\n".join(parts)
