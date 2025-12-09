from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request

app= FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print ("incoming request:", request.url)
    response = await call_next(request)
    return response


