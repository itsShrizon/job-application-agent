from app.core.parser import read_personal_md, validate_personal_md


def get_profile() -> dict:
    return read_personal_md()


def validate_profile() -> dict:
    return validate_personal_md()


def update_profile(profile_data: dict) -> dict:
    from app.core.parser import write_personal_md
    # Merge existing profile with updates
    current_profile = get_profile()
    updated_profile = {**current_profile, **profile_data}
    write_personal_md(updated_profile)
    return updated_profile
