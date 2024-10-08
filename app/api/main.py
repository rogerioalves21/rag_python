from fastapi import APIRouter
from app.api.routes import get_signed_url, user_control_service, check_documents, conversation

api_router = APIRouter()

# endpoints
api_router.include_router(get_signed_url.router, tags=["get-signed-url"])
api_router.include_router(user_control_service.router, tags=["user-control-service"])
api_router.include_router(check_documents.router, tags=["check-documents"])
api_router.include_router(conversation.router, tags=["conversation"])