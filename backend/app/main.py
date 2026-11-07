import logging
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ingestion.pdf_loader import extract_text_from_pdf
from app.chunking.text_splitter import chunk_documents
from app.vectorstore.chroma_store import store_chunks
from app.retrieval.retriever import retrieve_relevant_chunks
from app.pipeline.rag_pipeline import answer_question


# --------------------------------------------------
# Logging
# --------------------------------------------------

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

app = FastAPI(
    title="NEXORA AI - Advanced Document Intelligence",
    description="RAG-powered document question-answering API",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_QUESTION_LENGTH = 500
MIN_TOP_K = 1
MAX_TOP_K = 10


# --------------------------------------------------
# Request validation
# --------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=MAX_QUESTION_LENGTH,
        description="Question to search for in uploaded documents"
    )
    document_id: str | None = Field(
        default=None,
        pattern=r"^[a-fA-F0-9]{32}$",
        description="Optional document ID returned by the upload endpoint"
    )
    top_k: int = Field(
        default=3,
        ge=MIN_TOP_K,
        le=MAX_TOP_K,
        description="Number of document chunks to retrieve (1-10)"
    )


def validate_question(query: str) -> str:
    """Reject blank questions and return a trimmed question."""
    cleaned_query = query.strip()

    if not cleaned_query:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid question."
        )

    if len(cleaned_query) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Question cannot exceed {MAX_QUESTION_LENGTH} characters."
        )

    return cleaned_query


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "NEXORA AI API is running!",
        "status": "healthy"
    }


# --------------------------------------------------
# PDF upload and ingestion
# --------------------------------------------------

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a PDF file."
        )

    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    document_id = uuid4().hex
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        # Read at most 10 MB + 1 byte so oversized files are detected.
        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF is empty."
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="PDF file is too large. Maximum allowed size is 10 MB."
            )

        # Check the PDF file signature instead of trusting the extension alone.
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="The uploaded file does not appear to be a valid PDF."
            )

        # Save the PDF using a generated ID, not the user's filename.
        file_path.write_bytes(content)

        # Step 1: Extract text from the PDF.
        pages = extract_text_from_pdf(str(file_path))

        if not pages:
            raise HTTPException(
                status_code=422,
                detail="No readable text was found in the PDF."
            )

        # Step 2: Divide extracted text into chunks.
        chunks = chunk_documents(pages)

        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="No text chunks could be created from this PDF."
            )

        # Step 3: Generate embeddings and store chunks in ChromaDB.
        stored_chunks = store_chunks(chunks, document_id)

        return {
            "message": "PDF processed and stored successfully!",
            "document_id": document_id,
            "filename": Path(file.filename).name,
            "total_pages": len(pages),
            "total_chunks": len(chunks),
            "stored_chunks": stored_chunks
        }

    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise

    except ValueError as error:
        if file_path.exists():
            file_path.unlink()

        logger.warning("PDF processing failed: %s", error)
        raise HTTPException(
            status_code=422,
            detail="The PDF could not be processed. Check that it is readable and not corrupted."
        ) from error

    except Exception as error:
        if file_path.exists():
            file_path.unlink()

        logger.exception("Unexpected error while processing uploaded PDF")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the PDF."
        ) from error

    finally:
        await file.close()


# --------------------------------------------------
# Search uploaded documents
# --------------------------------------------------

@app.post("/documents/search")
def search_documents(request: SearchRequest):

    query = validate_question(request.query)

    try:
        chunks = retrieve_relevant_chunks(
            query=query,
            top_k=request.top_k,
            document_id=request.document_id
        )

        return {
            "query": query,
            "total_results": len(chunks),
            "results": chunks
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        logger.exception("Document search failed")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while searching documents."
        ) from error


# --------------------------------------------------
# Ask questions using the RAG pipeline
# --------------------------------------------------

@app.post("/documents/ask")
def ask_documents(request: SearchRequest):

    query = validate_question(request.query)

    try:
        result = answer_question(
            query=query,
            top_k=request.top_k,
            document_id=request.document_id
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        logger.exception("RAG question-answering failed")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the answer."
        ) from error
