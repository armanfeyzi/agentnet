from agentnet_mcp.schemas import ExperienceSummary, SearchExperiencesResponse


def format_search_results(response: SearchExperiencesResponse) -> str:
    if not response.results:
        return "No matching experiences found."

    lines: list[str] = []
    total = response.total if response.total is not None else len(response.results)
    lines.append(f"Found {total} experience(s):\n")

    for index, summary in enumerate(response.results, start=1):
        lines.append(_format_summary(index, summary))

    return "\n".join(lines)


def _format_summary(index: int, summary: ExperienceSummary) -> str:
    tags = ", ".join(summary.capability_tags) if summary.capability_tags else "none"
    success = "unknown" if summary.success is None else ("yes" if summary.success else "no")
    visibility = summary.visibility or "unknown"

    return (
        f"{index}. [{summary.id}]\n"
        f"   Task: {summary.task}\n"
        f"   Problem: {summary.problem_summary}\n"
        f"   Tags: {tags}\n"
        f"   Success: {success} | Visibility: {visibility}"
    )
