from fastapi import FastAPI
from app.controllers.video_controller import router as video_router
from app.controllers.upload_controller import router as upload_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(video_router)
app.include_router(upload_router)

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI Video Processing Server"}
