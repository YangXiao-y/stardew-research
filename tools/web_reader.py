import requests
from bs4 import BeautifulSoup
from config import settings


def fetch_page_html_browserless(url: str, timeout: int = 45) -> str:
    endpoint = f"{settings.BROWSERLESS_BASE_URL}/content?token={settings.BROWSERLESS_API_KEY}"
    payload = {
        "url": url
    }
    headers = {
        "Content-Type": "application/json"
    }

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return text[:20000]


def fetch_page_text(url: str, timeout: int = 45) -> str:
    html = fetch_page_html_browserless(url, timeout=timeout)
    return clean_html_to_text(html)