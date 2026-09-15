from fastapi import FastAPI
from app.database import Base, engine
from app.routers.upload import router as upload_router
from app.routers.history import router as history_router
from app.routers.files import router as files_router

app = FastAPI(title="Audio Processing API")

Base.metadata.create_all(bind=engine)

app.include_router(upload_router, prefix="/api", tags=["audio"])
app.include_router(history_router, prefix="/api", tags=["audio"])
app.include_router(files_router, prefix="/api", tags=["audio"])
