from urllib.parse import urlparse


def detect_source_type(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "stardewvalleywiki" in domain:
        return "wiki"
    if "steamcommunity" in domain:
        return "guide"
    if "reddit" in domain or "forum" in domain:
        return "forum"
    return "other"