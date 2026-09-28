import jinja2


STATIC_ROOT = "src/lead_gen/static"
TEMPLATE_ROOT = "src/lead_gen/templates"


env = jinja2.Environment(
    loader=jinja2.loaders.FileSystemLoader(TEMPLATE_ROOT),
)


def pad(value, char: str, length: int) -> str:
    value = str(value)

    if len(value) >= length:
        return value
    else:
        return char * (length - len(value)) + value


env.filters["pad"] = pad
