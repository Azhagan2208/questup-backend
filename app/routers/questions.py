from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..deps import get_db, get_current_teacher

router = APIRouter(tags=["Questions"])


@router.post("/rooms/{room_id}/questions")
def post_question(
    room_id: int, data: schemas.QuestionCreate, db: Session = Depends(get_db)
):
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.is_open == True)
        .first()
    )
    if not room:
        return {"success": False, "detail": "Room not found or closed"}
    q = models.Question(
        room_id=room_id,
        title=data.title,
        description=data.description,
        student_name=data.student_name,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"success": True, "question": schemas.QuestionOut.from_orm(q)}


@router.get("/rooms/{room_id}/questions")
def list_room_questions(
    room_id: int, db: Session = Depends(get_db), sort: str = "recent"
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        return {"success": False, "detail": "Room not found"}

    questions_query = (
        db.query(models.Question).filter(models.Question.room_id == room_id).all()
    )

    results = []
    for q in questions_query:
        vote_count = (
            db.query(models.QuestionVote)
            .filter(
                models.QuestionVote.question_id == q.id,
                models.QuestionVote.vote_type == "up",
            )
            .count()
        )
        q_out = schemas.QuestionOut.from_orm(q)
        q_out.votes = vote_count
        results.append(q_out)

    if sort == "votes":
        results.sort(key=lambda x: x.votes, reverse=True)
    else:
        results.sort(key=lambda x: x.created_at, reverse=True)

    return {
        "success": True,
        "questions": results,
    }


@router.get("/questions/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        return {"success": False, "detail": "Question not found"}

    votes = (
        db.query(models.QuestionVote)
        .filter(
            models.QuestionVote.question_id == q.id,
            models.QuestionVote.vote_type == "up",
        )
        .count()
    )

    answers = (
        db.query(models.Answer)
        .filter(models.Answer.question_id == q.id)
        .order_by(models.Answer.created_at.asc())
        .all()
    )

    q_out = schemas.QuestionOut.from_orm(q)
    q_out.votes = votes

    return {
        "success": True,
        "question": q_out,
        "answers": [schemas.AnswerOut.from_orm(a) for a in answers],
    }


@router.patch("/questions/{question_id}")
def edit_question(
    question_id: int,
    data: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    q = (
        db.query(models.Question)
        .join(models.Room)
        .filter(models.Question.id == question_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not q:
        return {"success": False, "detail": "Question not found or you're not owner"}
    q.title = data.title
    q.description = data.description
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"success": True, "question": schemas.QuestionOut.from_orm(q)}


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    q = (
        db.query(models.Question)
        .join(models.Room)
        .filter(models.Question.id == question_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not q:
        return {"success": False, "detail": "Question not found or you're not owner"}
    db.delete(q)
    db.commit()
    return {"success": True, "message": "Question deleted"}


@router.post("/questions/{question_id}/report")
def report_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        return {"success": False, "detail": "Question not found"}
    return {"success": True, "message": "Reported (admin will review)"}


@router.post("/questions/{question_id}/solve")
def mark_solved(
    question_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    q = (
        db.query(models.Question)
        .join(models.Room)
        .filter(models.Question.id == question_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not q:
        return {"success": False, "detail": "Question not found or you're not owner"}
    q.is_solved = True
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"success": True, "question": schemas.QuestionOut.from_orm(q)}
