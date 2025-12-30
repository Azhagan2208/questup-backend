from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from typing import Optional


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_teacher(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_token: Optional[str] = Header(None, alias="x-token"),
    db: Session = Depends(get_db),
):
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token and x_token:
        token = x_token

    if not token:
        return None

    teacher = db.query(models.Teacher).filter(models.Teacher.token == token).first()
    return teacher
