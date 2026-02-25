from app.models import (
    audit_event,
    user,
    session,
    chat_message,
    project,
    resource,
    security_alert,
    software_package,
    file_blob,
    file_version,
    upload_session,
)
from app.database.db_setup import Base, engine
from asyncio.log import logger

def init_db():
  try:
      Base.metadata.create_all(bind=engine)
      # Base.metadata.drop_all(bind=engine)
  except Exception as e:
    logger.exception(f"[-] Failed to create database tables: {e}")
