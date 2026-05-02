from secrets import token_urlsafe


def new_id(prefix: str) -> str:
    normalized_prefix = prefix if prefix.endswith("_") else f"{prefix}_"
    return f"{normalized_prefix}{token_urlsafe(16)}"

