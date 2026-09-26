def get_credentials(service: str) -> str | None:
    try:
        file = open(f".{service}-api-key.txt", "r")
        key = file.read()
        file.close()
        return key

    except FileNotFoundError:
        return None


def set_credentials(service: str, key: str):
    file = open(f".{service}-api-key.txt", "w+")
    file.write(key)
    file.close()
