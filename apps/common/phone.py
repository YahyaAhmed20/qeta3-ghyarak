import re


EGYPT_COUNTRY_CODE = "20"
EGYPT_MOBILE_PREFIXES = ("10", "11", "12", "15")


def normalize_egyptian_phone(phone: str) -> str:
    """
    Normalize Egyptian mobile numbers to E.164 format.

    Examples:
        01012345678      -> +201012345678
        201012345678     -> +201012345678
        +201012345678    -> +201012345678
        +20 101 234 5678 -> +201012345678
    """
    if not phone:
        raise ValueError("Phone number is required.")

    phone = str(phone).strip()

    # Keep digits only, while removing spaces, dashes, parentheses, etc.
    digits = re.sub(r"\D", "", phone)

    if digits.startswith(EGYPT_COUNTRY_CODE):
        national_number = digits[2:]
    elif digits.startswith("0"):
        national_number = digits[1:]
    else:
        national_number = digits

    if len(national_number) != 10:
        raise ValueError("Invalid Egyptian mobile number.")

    if not national_number.startswith(EGYPT_MOBILE_PREFIXES):
        raise ValueError("Invalid Egyptian mobile number.")

    return f"+{EGYPT_COUNTRY_CODE}{national_number}"