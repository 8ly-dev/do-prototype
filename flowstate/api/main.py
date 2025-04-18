from fastapi import FastAPI
from contextlib import asynccontextmanager
from flowstate.db_models import init_db
from flowstate.api.routers import auth, projects, tasks, settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Initialize database
    yield

app = FastAPI(lifespan=lifespan, title="Flowstate API", version="0.1.0")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(settings.router, prefix="/settings", tags=["User Settings"])
