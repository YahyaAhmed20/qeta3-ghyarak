def normalize_vin(value: str) -> str:
    if not value:
        return ""

    return value.replace(" ", "").upper()