from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from passlib.context import CryptContext
import uuid

from ..database import SessionLocal
from .. import models, schemas
from ..deps import get_current_teacher

router = APIRouter(prefix="/auth/teachers", tags=["Teacher Auth"])
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False
)

ADMIN_SECRET = "adminsecret"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(pw: str) -> str:
    if not pw or len(pw) == 0:
        raise ValueError("Password cannot be empty")

    # Bcrypt has a 72-byte limit. We must truncate BYTES, not characters.
    # 1. Encode to bytes (utf-8)
    pw_bytes = pw.encode("utf-8")

    # 2. Truncate if longer than 72 bytes
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]

    # 3. Decode back to string for passlib, ignoring any partial multi-byte character at the end
    # using 'ignore' avoids errors if we cut a unicode char in half.
    # Note: passlib will encode it again, but now we know it fits!
    truncated_pw = pw_bytes.decode("utf-8", errors="ignore")

    return pwd_context.hash(truncated_pw)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


@router.post("/request-access")
def request_access(data: schemas.TeacherRequestCreate, db: Session = Depends(get_db)):
    # Hash the password provided by the user
    hashed_pw = hash_password(data.password)
    req = models.TeacherRequest(
        name=data.name, email=data.email, password_hash=hashed_pw
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"success": True, "message": "Request submitted", "request_id": req.id}


@router.post("/register")
def register_teacher(
    data: schemas.TeacherRegister, admin_secret: str = "", db: Session = Depends(get_db)
):
    if admin_secret != ADMIN_SECRET:
        return {"success": False, "detail": "Admin secret required"}
    existing = (
        db.query(models.Teacher).filter(models.Teacher.email == data.email).first()
    )
    if existing:
        return {"success": False, "detail": "Email already registered"}
    t = models.Teacher(
        name=data.name, email=data.email, password_hash=hash_password(data.password)
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"success": True, "teacher": schemas.TeacherOut.from_orm(t)}


@router.post("/login")
def login(data: schemas.TeacherLogin, db: Session = Depends(get_db)):
    teacher = (
        db.query(models.Teacher).filter(models.Teacher.email == data.email).first()
    )
    if not teacher or not verify_password(data.password, teacher.password_hash):
        return {"success": False, "detail": "Invalid credentials"}
    token = uuid.uuid4().hex
    teacher.token = token
    db.add(teacher)
    db.commit()
    return {
        "success": True,
        "token": token,
        "teacher": schemas.TeacherOut.from_orm(teacher),
    }


@router.get("/me")
def me(teacher: models.Teacher = Depends(get_current_teacher)):
    if not teacher:
        return {"success": False, "detail": "Invalid token or not logged in"}
    return {
        "success": True,
        "teacher": {"id": teacher.id, "name": teacher.name, "email": teacher.email},
    }


@router.post("/logout")
def logout(
    teacher: models.Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    if not teacher:
        return {"success": False, "detail": "Invalid token or not logged in"}
    teacher.token = None
    db.add(teacher)
    db.commit()
    return {"success": True, "message": "Logged out"}


@router.post("/admin/login")
def admin_login(data: schemas.TeacherLogin):
    """
    Simple admin login.
     Hardcoded credentials for demonstration:
    Email: admin@questup.com
    Password: admin123
    """
    if data.email == "admin@questup.com" and data.password == "admin123":
        return {"success": True, "token": ADMIN_SECRET}

    raise HTTPException(status_code=401, detail="Invalid admin credentials")


@router.post("/admin-check")
def check_admin(x_admin_secret: str = Header(...)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    return {"success": True}


# --------------------------------------------------------------------------
# ADMIN : APPROVE REQUEST (Protected by Secret Key)
# --------------------------------------------------------------------------


@router.get("/requests")
def list_requests(x_admin_secret: str = Header(...), db: Session = Depends(get_db)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    pending_reqs = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.approved == False)
        .order_by(models.TeacherRequest.created_at.desc())
        .all()
    )

    approved_reqs = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.approved == True)
        .order_by(models.TeacherRequest.created_at.desc())
        .all()
    )

    stats = {
        "pending": len(pending_reqs),
        "approved": len(approved_reqs),
        "total": len(pending_reqs) + len(approved_reqs),
    }

    return {
        "success": True,
        "requests": pending_reqs,
        "history": approved_reqs,
        "stats": stats,
    }


@router.post("/approve/{request_id}")
def approve_request(
    request_id: int,
    data: schemas.ApproveRequest,
    db: Session = Depends(get_db),
    x_admin_secret: str = Header(...),
):
    """Approve a teacher request and create their account"""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid admin secret")

    # Get the request
    req = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.id == request_id)
        .first()
    )
    if not req:
        return {"success": False, "detail": "Request not found"}

    if req.approved:
        return {"success": False, "detail": "Request already approved"}

    # Check if teacher already exists
    existing = (
        db.query(models.Teacher).filter(models.Teacher.email == req.email).first()
    )
    if existing:
        return {"success": False, "detail": "Teacher with this email already exists"}

    try:
        # Create teacher account
        teacher = models.Teacher(
            name=req.name, email=req.email, password_hash=req.password_hash
        )
        db.add(teacher)

        # Mark request as approved
        req.approved = True
        db.add(req)

        db.commit()
        db.refresh(teacher)

        return {
            "success": True,
            "message": "Teacher approved and account created",
            "teacher": schemas.TeacherOut.from_orm(teacher),
        }
    except ValueError as e:
        return {"success": False, "detail": f"Password error: {str(e)}"}
    except Exception as e:
        db.rollback()
        return {"success": False, "detail": f"Error creating teacher account: {str(e)}"}
