"""
Green Habitat Certification Backend
====================================
Entry point for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import rating

app = FastAPI(
    title="Green Habitat Certification API",
    description="Environmental livability certification system for residential areas.",
    version="1.0.0",
)

# Allow all origins for development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(rating.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Green Habitat Certification API is running."}
