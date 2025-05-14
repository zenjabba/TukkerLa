from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine
import app.models.base as models
from app.routers import auth, items, images, barcodes, categories, locations
from app.config import settings

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="TuckerLa Freezer Tracker",
    description="API for managing freezer food inventory with image and barcode support",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(images.router)
app.include_router(barcodes.router)
app.include_router(categories.router)
app.include_router(locations.router)


@app.get("/", tags=["root"])
def read_root():
    """Root endpoint that returns a welcome message."""
    return {
        "message": "Welcome to TuckerLa Freezer Tracker API",
        "docs_url": "/docs",
        "version": "1.0.0"
    }


# For debugging purposes, show loaded routes
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 