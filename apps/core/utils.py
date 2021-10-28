def is_phone(value):
    if len(value) < 10 \
            or value[0] != "0" \
            or not value.isnumeric():
        return False
    return True


def is_valid_name(value: str):
    if not value:
        return True

    for c in value.replace(" ", ""):
        if not c.isalpha():
            return False
    return True
