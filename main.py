from fastapi import FastAPI
import uvicorn
from authentication import signup, login, verify, password_reset
from manage_files import upload_file, download_file, list_file, delete_file
from Database import models
from Database.data import engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


app.include_router(signup.router)
app.include_router(login.router)
app.include_router(verify.router)
app.include_router(password_reset.router)
app.include_router(upload_file.router)

app.include_router(download_file.router)
app.include_router(list_file.router)
app.include_router(delete_file.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
