from src.llm import LLMService

UNSUPPORTED = "UNSUPPORTED"


async def analyze_query(text: str) -> str:
    """
    Turn a natural-language request into a GitHub search query string.

    Returns the query (e.g. "machine learning language:python stars:>=50"),
    or UNSUPPORTED if the request can't be expressed as a GitHub search.
    """
    system = (
        "You are a GitHub search interpreter. You will be given a user query describing "
        "the repositories they are looking for. "
        "Extract the main keywords and any qualifiers the user wants to search GitHub "
        "repositories by, such as language, stars or forks. "
        "Respond with only the GitHub search query, nothing else. "
        f"If the query is not supported, respond with only '{UNSUPPORTED}'."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]

    resp = await LLMService.active_llm().ainvoke(messages)
    return resp.text.strip()
