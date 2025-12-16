from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.database import engine
from app.models import models
from app.api.v1.endpoints import auth, files

app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print("incoming request:", request.url)
    response = await call_next(request)
    return response

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(files.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
