from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Any
from app.config import RagService
from app.api.services.comunicados_service import ComunicadosService

router = APIRouter()

async def _proccess_task(__rag_service: ComunicadosService | None) -> None:
    try:
        await __rag_service.load_data()
    except Exception as e:
        print("ERRO")
        print(e)


@router.get("/load-data", dependencies=[RagService])
async def load_data(background_tasks: BackgroundTasks, __rag_service: ComunicadosService | None = RagService) -> Any:
    background_tasks.add_task(_proccess_task, __rag_service)
    return JSONResponse(content={"success": True})
    