from typing import Annotated

from fastapi import APIRouter, Query, Cookie

from lead_gen import zoho
from lead_gen.database import Project, Sequence


router = APIRouter()


@router.get("/oauth/zoho/callback")
async def handle_oauth_zoho_callback(
    code: str,
    location: str,
    accounts_server: Annotated[str, Query(alias="accounts-server")],
    connect_project_id: Annotated[str, Cookie()],
    connect_sequence_id: Annotated[str, Cookie()],
):
    
    pass
