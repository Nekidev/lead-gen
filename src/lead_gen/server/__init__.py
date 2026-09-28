from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response, HTMLResponse
from fastapi.exceptions import HTTPException

from tortoise.context import TortoiseContext

from lead_gen import website
from lead_gen.website import env
from lead_gen.database import CONFIG, Project
from lead_gen.server.projects import router as projects_router
from lead_gen.server.connections import router as connections_router


@asynccontextmanager
async def context(app: FastAPI):
    async with TortoiseContext() as ctx:
        await ctx.init(config=CONFIG, _enable_global_fallback=True)
        yield


app = FastAPI(lifespan=context)

app.include_router(projects_router)
app.include_router(connections_router)


@app.get("/")
async def get_index():
    projects = await Project.all()

    template = env.get_template("index.html.j2")
    response = HTMLResponse(template.render({"projects": projects}))
    return response


@app.get("/static/{path:path}")
def get_file(path: str):
    for segment in path.split("/"):
        if segment in [".", ".."]:
            raise HTTPException(422, "The path cannot contain . nor .. segments.")

    path = website.STATIC_ROOT + "/" + path

    contents = read_to_string(path)
    if contents is None:
        if not path.endswith("/"):
            path += "/"

        path += "index.html"
        contents = read_to_string(path)

    if contents is None:
        raise HTTPException(404, "The file you requested was not found.")

    template = env.from_string(contents)
    contents = template.render()

    response = Response(contents)
    match path.rsplit(".", 1)[-1]:
        case "html":
            response.headers["content-type"] = "text/html"
        case "js":
            response.headers["content-type"] = "text/javascript"
        case "css":
            response.headers["content-type"] = "text/css"
        case _:
            response.headers["content-type"] = "text/plain"

    return response


def read_to_string(path: str) -> str | None:
    try:
        file = open(path, "r")
        return file.read()

    except (FileNotFoundError, IsADirectoryError):
        return None
