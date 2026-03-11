from app.core.parser import read_personal_md, validate_personal_md


def get_profile() -> dict:
    return read_personal_md()


def validate_profile() -> dict:
    return validate_personal_md()
