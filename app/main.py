from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import upload_controller, analysis_controller

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_controller.router)
app.include_router(analysis_controller.router)

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI Video Processing Server"}
