from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..deps import get_db

router = APIRouter(tags=["Votes"])


@router.post("/questions/{question_id}/vote")
def vote_question(
    question_id: int, data: schemas.VoteCreate, db: Session = Depends(get_db)
):
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        return {"success": False, "detail": "Question not found"}
    if data.vote_type not in ("up", "down"):
        return {"success": False, "detail": "vote_type must be 'up' or 'down'"}
    v = models.QuestionVote(
        question_id=question_id, voter_token=data.voter_token, vote_type=data.vote_type
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"success": True, "vote_id": v.id}


@router.get("/questions/{question_id}/votes")
def get_question_votes(question_id: int, db: Session = Depends(get_db)):
    up = (
        db.query(models.QuestionVote)
        .filter(
            models.QuestionVote.question_id == question_id,
            models.QuestionVote.vote_type == "up",
        )
        .count()
    )
    down = (
        db.query(models.QuestionVote)
        .filter(
            models.QuestionVote.question_id == question_id,
            models.QuestionVote.vote_type == "down",
        )
        .count()
    )
    return {"success": True, "question_id": question_id, "up": up, "down": down}
