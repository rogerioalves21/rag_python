from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any
from app.config import RagService
from app.api.services.comunicados_service import ComunicadosService

router = APIRouter()

@router.get("/load-data", dependencies=[RagService])
async def load_data(__rag_service: ComunicadosService | None = RagService) -> Any:
    try:
        await __rag_service.load_data()
        return JSONResponse(content={"success": True})
    except Exception as e:
        print("ERRO")
        print(e)
        return JSONResponse(content=str(e), status_code=400)