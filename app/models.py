from pydantic import BaseModel
from typing import Union, Any, List

class SignedUrls(BaseModel):
    presigned_urls: Union[list[str] | None] = None

class User(BaseModel):
    cooperativa: Union[str | None] = None
    email: Union[str | None] = None
    login: Union[str | None] = None
    descricao: Union[str | None] = None
    cpfCnpj: Union[str | None] = None
    instituicaoOrigem: Union[str | None] = None

class UserControlServicePayload(BaseModel):
    file_key: Union[str | None] = None
    service: Union[str | None] = None

class UserControlServiceResponse(BaseModel):
    message: Union[str | None] = None

class DocumentContent(BaseModel):
    _id: Union[str | None] = None
    date_time: Union[str | None] = None
    expireAt: Union[str | None] = None
    embeddings: Union[list[list[float]] | None] = None
    file_content: Union[str | None] = None
    file_key: Union[str | None] = None
    service: Union[str | None] = None
    user_id: Union[str | None] = None

class CheckDocumentsPayload(BaseModel):
    file_key: Union[str | None] = None
    service: Union[str | None] = None

class CheckDocumentsResponse(BaseModel):
    count: Union[int | None] = None
    documents: Union[list[DocumentContent] | None] = None

class DescriptionModel(BaseModel):
    type: Union[str | None] = None
    description: Union[str | None] = None

class PropertiesModel(BaseModel):
    question: Union[DescriptionModel | None] = None
    service: Union[DescriptionModel | None] = None
    model: Union[DescriptionModel | None] = None

class SourceModel(BaseModel):
    name: Union[str | None] = None
    link: Union[str | None] = None
    page: Union[int | None] = 0
    topic_suggestions: Union[str, None] = None

class ConversationPayload(BaseModel):
    type: Union[str | None] = None
    start_date: Union[str | None] = None
    end_date: Union[str | None] = None
    properties: Union[PropertiesModel | None] = None

class ConversationResponse(BaseModel):
    data: Union[str | None] = None
    success: bool = True

class NormativosResponse(BaseModel):
    message: Union[str | None] = None
    sources: Union[List | None] = None