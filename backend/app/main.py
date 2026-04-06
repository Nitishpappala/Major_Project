from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import dashboard, articles, channels, categories, trends, project_info, lineage

app = FastAPI(
    title="News Pipeline API",
    description="API for serving news data from Databricks gold_articles table",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(channels.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(project_info.router, prefix="/api")
app.include_router(lineage.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
