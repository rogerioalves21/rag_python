from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any
from app.config import RagService
from app.api.services.comunicados_service import ComunicadosService

router = APIRouter()

@router.get("/load-data", dependencies=[RagService])
def load_data(__rag_service: ComunicadosService | None = RagService) -> Any:
    __rag_service.load_data()
    return JSONResponse(content={"success": True})