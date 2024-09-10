from fastapi import APIRouter
from app.api.routes import (
    get_signed_url,
    user_control_service,
    check_documents,
    conversation,
    conversation2,
    parent,
    load_data,
    conversation_normativos,
    data_analysis
)

api_router = APIRouter()

# endpoints
api_router.include_router(get_signed_url.router, tags=["get-signed-url"])
api_router.include_router(user_control_service.router, tags=["user-control-service"])
api_router.include_router(check_documents.router, tags=["check-documents"])
api_router.include_router(conversation.router, tags=["conversation"])
api_router.include_router(conversation2.router, tags=["conversation-tiny"])
api_router.include_router(parent.router, tags=["conversation-parent"])
api_router.include_router(data_analysis.router, tags=["data-analysis"])
api_router.include_router(conversation_normativos.router, tags=["conversation-with-sources"])
api_router.include_router(load_data.router, tags=["load-data"])