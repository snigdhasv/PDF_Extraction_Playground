import modal
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

# Add extractors directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal app
app = modal.App("pdf-extraction-playground")

# Define Modal image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("poppler-utils", "tesseract-ocr")  # Required for some PDF processing
    .pip_install(
        "fastapi[standard]==0.115.0",
        "python-multipart==0.0.9",
        "pillow==10.4.0",
        "pypdf==4.3.1",
        "python-magic==0.4.27",
        "docling==2.5.2",  # Docling for PDF extraction
        "pydantic==2.9.0",
    )
)

# Mount local extractors directory
extractors_mount = modal.Mount.from_local_dir(
    local_path="./extractors",
    remote_path="/root/extractors"
)

# Create FastAPI instance
web_app = FastAPI(
    title="PDF Extraction Playground API",
    description="API for extracting content from PDF documents using multiple OCR models",
    version="1.0.0",
)

# CORS middleware
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@web_app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "message": "PDF Extraction Playground API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@web_app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "service": "pdf-extraction-api",
        "timestamp": datetime.utcnow().isoformat(),
        "models_available": ["docling", "surya", "mineru"]
    }

@web_app.get("/models")
async def list_models():
    """List available extraction models with their capabilities"""
    models = {
        "docling": {
            "name": "Docling",
            "description": "Document understanding and conversion framework",
            "capabilities": ["text", "tables", "layout", "structure"],
            "best_for": "General documents and structured content",
            "status": "available"
        },
        "surya": {
            "name": "Surya",
            "description": "Multilingual document OCR and layout analysis",
            "capabilities": ["text", "layout", "multilingual"],
            "best_for": "Multilingual documents and complex layouts",
            "status": "coming_soon"
        },
        "mineru": {
            "name": "MinerU",
            "description": "PDF extraction for scientific documents",
            "capabilities": ["text", "tables", "formulas", "figures"],
            "best_for": "Scientific papers and academic documents",
            "status": "coming_soon"
        }
    }
    return {"models": models}

@web_app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    model: Optional[str] = Form(default="docling")
):
    """
    Upload and validate PDF file
    
    Args:
        file: PDF file to process
        model: Extraction model to use (docling, surya, mineru)
    
    Returns:
        JSON with file info and validation status
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Validate file size (max 50MB)
        contents = await file.read()
        file_size = len(contents)
        max_size = 50 * 1024 * 1024  # 50MB
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds maximum allowed size of {max_size / (1024*1024):.1f}MB"
            )
        
        # Validate model selection
        valid_models = ["docling"]  # Only docling is implemented for now
        if model not in valid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Currently available: {', '.join(valid_models)}"
            )
        
        logger.info(f"Received PDF: {file.filename} ({file_size / 1024:.2f} KB)")
        
        return JSONResponse(content={
            "status": "success",
            "message": "PDF uploaded and validated successfully",
            "file_info": {
                "filename": file.filename,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "model_selected": model
            },
            "next_steps": "File ready for extraction. Call /extract endpoint."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@web_app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(...),
    model: str = Form(default="docling")
):
    """
    Extract content from PDF using selected model
    
    Args:
        file: PDF file to extract
        model: Extraction model (currently only 'docling' is available)
    
    Returns:
        Extracted content with markdown, elements, and bounding boxes
    """
    try:
        # Validate inputs
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file contents
        contents = await file.read()
        file_size = len(contents)
        
        # Size check
        max_size = 50 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        logger.info(f"Starting extraction for {file.filename} using {model}")
        
        # Route to appropriate extractor
        if model == "docling":
            from extractors.docling_extractor import DoclingExtractor
            extractor = DoclingExtractor()
            result = extractor.extract(contents, file.filename)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model}' not implemented yet. Use 'docling'."
            )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

# Deploy FastAPI app on Modal
@app.function(
    image=image,
    gpu=None,  # Start without GPU
    timeout=600,  # 10 minutes for PDF processing
    allow_concurrent_inputs=10,
    mounts=[extractors_mount],
)
@modal.asgi_app()
def fastapi_app():
    """Modal ASGI app wrapper for FastAPI"""
    return web_app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(web_app, host="0.0.0.0", port=8000)