from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers.auth import router as auth

from .routers.rooms import router as room
from .routers.questions import router as question
from .routers.answers import router as answer
from .routers.votes import router as vote

# creating the database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Questup Backend")

# # mounting the frontend static files
# app.mount("/css", StaticFiles(directory="../css"), name="css")
# app.mount("/js", StaticFiles(directory="../js"), name="js")
# app.mount("/pages", StaticFiles(directory="../pages", html=True), name="pages")
# app.mount("/assests", StaticFiles(directory="../assests"), name="assests")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)
app.include_router(room)
app.include_router(question)
app.include_router(answer)
app.include_router(vote)


# @app.get("/")
# async def read_index():
#     return FileResponse("../index.html")


# @app.get("/index.html")
# async def read_index_explicit():
#     return FileResponse("../index.html")


# @app.get("/admin")
# async def read_admin():
#     return FileResponse("../pages/admin-approve.html")


@app.get("/")
def home():
    return {"Questup" : "Api is running successfully!!!"}


@app.get("/health")
def health():
    return {"status": "ok"}
