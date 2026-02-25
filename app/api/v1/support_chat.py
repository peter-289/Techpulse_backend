from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.unit_of_work import UnitOfWork
from app.database.db_setup import get_db
from app.schemas.support_chat import SupportChatMessageRead, SupportChatRequest, SupportChatResponse
from app.services.support_chat_service import SupportChatService

router = APIRouter(prefix="/api/v1/support-chat", tags=["Support Chat"])


def get_service(db: Session = Depends(get_db)) -> SupportChatService:
    return SupportChatService(UnitOfWork(session=db))


@router.post("/messages", response_model=SupportChatResponse, status_code=201)
def send_message(
    payload: SupportChatRequest,
    service: SupportChatService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    message = service.ask(user_id=int(current_user["user_id"]), message=payload.message)
    return {"message_id": message.id, "assistant_reply": message.assistant_message}


@router.get("/messages", response_model=list[SupportChatMessageRead], status_code=200)
def list_messages(
    limit: int = Query(25, ge=1, le=100),
    service: SupportChatService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.list_messages(user_id=int(current_user["user_id"]), limit=limit)

