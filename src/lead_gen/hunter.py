from typing import TypedDict

from httpx import AsyncClient


_client = AsyncClient()


class Lead(TypedDict):
    id: int
    email: str
    first_name: str
    last_name: str
    position: str | None
    company: str
    company_industry: str | None
    company_size: str | None
    website: str


async def list_leads(api_key: str) -> list[Lead]:
    global _client

    response = await _client.get(
        "https://api.hunter.io/v2/leads",
        params={
            "api_key": api_key,
            "limit": 1000,
        },
    )
    response.raise_for_status()

    data = response.json()
    return data["data"]["leads"]
