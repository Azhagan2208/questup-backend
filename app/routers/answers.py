from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..deps import get_db, get_current_teacher

router = APIRouter(tags=["Answers"])


@router.post("/questions/{question_id}/answers")
def post_answer(
    question_id: int,
    data: schemas.AnswerCreate,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        return {"success": False, "detail": "Question not found"}
    ans = models.Answer(
        question_id=question_id, teacher_id=teacher.id, content=data.content
    )
    db.add(ans)
    db.commit()
    db.refresh(ans)
    return {"success": True, "answer": schemas.AnswerOut.from_orm(ans)}


@router.get("/questions/{question_id}/answers")
def list_answers(question_id: int, db: Session = Depends(get_db)):
    answers = (
        db.query(models.Answer).filter(models.Answer.question_id == question_id).all()
    )
    return {
        "success": True,
        "answers": [schemas.AnswerOut.from_orm(a) for a in answers],
    }


@router.patch("/answers/{answer_id}")
def edit_answer(
    answer_id: int,
    data: schemas.AnswerCreate,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    a = (
        db.query(models.Answer)
        .filter(models.Answer.id == answer_id, models.Answer.teacher_id == teacher.id)
        .first()
    )
    if not a:
        return {"success": False, "detail": "Answer not found or you're not author"}
    a.content = data.content
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"success": True, "answer": schemas.AnswerOut.from_orm(a)}


@router.delete("/answers/{answer_id}")
def delete_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    a = (
        db.query(models.Answer)
        .filter(models.Answer.id == answer_id, models.Answer.teacher_id == teacher.id)
        .first()
    )
    if not a:
        return {"success": False, "detail": "Answer not found or you're not author"}
    db.delete(a)
    db.commit()
    return {"success": True, "message": "Answer deleted"}


@router.post("/answers/{answer_id}/accept")
def accept_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    if not teacher:
        return {"success": False, "detail": "Unauthorized"}
    a = (
        db.query(models.Answer)
        .join(models.Question)
        .join(models.Room)
        .filter(models.Answer.id == answer_id, models.Room.owner_id == teacher.id)
        .first()
    )
    if not a:
        return {
            "success": False,
            "detail": "Answer not found or you're not question owner",
        }
    db.query(models.Answer).filter(models.Answer.question_id == a.question_id).update(
        {"is_accepted": False}
    )
    a.is_accepted = True
    db.add(a)
    q = db.query(models.Question).filter(models.Question.id == a.question_id).first()
    q.is_solved = True
    db.add(q)
    db.commit()
    db.refresh(a)
    return {"success": True, "answer": schemas.AnswerOut.from_orm(a)}
