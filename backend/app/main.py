from fastapi import FastAPI
from app.database import Base, engine

app = FastAPI(title="Audio Processing API")

Base.metadata.create_all(bind=engine)