from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from .. import models, schemas
from ..deps import get_db, get_current_teacher

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def gen_room_code():
    return uuid.uuid4().hex[:6].upper()


@router.post("")
def create_room(
    data: schemas.RoomCreate,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    code = gen_room_code()
    while db.query(models.Room).filter(models.Room.room_code == code).first():
        code = gen_room_code()

    room = models.Room(
        title=data.title,
        subject_id=data.subject_id,
        room_code=code,
        owner_id=teacher.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return schemas.RoomOut.from_orm(room)


@router.get("")
def list_rooms(
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    rooms = db.query(models.Room).filter(models.Room.owner_id == teacher.id).all()
    return {"success": True, "rooms": [schemas.RoomOut.from_orm(r) for r in rooms]}


@router.get("/{room_id}")
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not room:
        return {"success": False, "detail": "Room not found"}
    return schemas.RoomOut.from_orm(room)


@router.patch("/{room_id}")
def update_room(
    room_id: int,
    data: schemas.RoomCreate,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not room:
        return {"success": False, "detail": "Room not found"}
    room.title = data.title
    room.subject_id = data.subject_id
    db.add(room)
    db.commit()
    db.refresh(room)
    return {"success": True, "room": schemas.RoomOut.from_orm(room)}


@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not room:
        return {"success": False, "detail": "Room not found"}
    db.delete(room)
    db.commit()
    return {"success": True, "message": "Room deleted"}


@router.post("/{room_id}/close")
def close_room(
    room_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not room:
        return {"success": False, "detail": "Room not found"}
    room.is_open = False
    db.add(room)
    db.commit()
    db.refresh(room)
    return {"success": True, "room": schemas.RoomOut.from_orm(room)}


@router.post("/join")
def join_by_code(payload: dict, db: Session = Depends(get_db)):
    code = payload.get("room_code")
    if not code:
        return {"success": False, "detail": "room_code required"}
    room = (
        db.query(models.Room)
        .filter(models.Room.room_code == code, models.Room.is_open == True)
        .first()
    )
    if not room:
        return {"success": False, "detail": "Room not found or closed"}
    return {"success": True, "room": schemas.RoomOut.from_orm(room)}
