import jinja2


STATIC_ROOT = "src/lead_gen/static"
TEMPLATE_ROOT = "src/lead_gen/templates"


env = jinja2.Environment(
    loader=jinja2.loaders.FileSystemLoader(TEMPLATE_ROOT),
)
