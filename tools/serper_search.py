import time
import requests
from requests.exceptions import ReadTimeout, RequestException
from config import settings
from core.schemas import SearchResultItem

SERPER_URL = "https://google.serper.dev/search"


def serper_search(query: str, num: int = 5, max_retries: int = 3, timeout: int = 60) -> list[SearchResultItem]:
    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num
    }

    last_error = None

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                SERPER_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()

            items = []
            for x in data.get("organic", [])[:num]:
                items.append(SearchResultItem(
                    title=x.get("title", ""),
                    link=x.get("link", ""),
                    snippet=x.get("snippet", "")
                ))
            return items

        except ReadTimeout as e:
            last_error = e
            wait_time = 2 ** attempt
            time.sleep(wait_time)

        except RequestException as e:
            last_error = e
            wait_time = 2 ** attempt
            time.sleep(wait_time)

    print(f"[Serper Error] query={query} failed after {max_retries} retries: {last_error}")
    return []