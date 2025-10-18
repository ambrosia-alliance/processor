from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import (
    ClassificationRequest,
    ClassificationResponse,
    HealthResponse,
    CategoriesResponse
)
from app.pipeline.chunker import SentenceChunker
from app.pipeline.classifier import TherapyClassifier
from app.pipeline.aggregator import ResultAggregator


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chunker = None
classifier = None
aggregator = None


@app.on_event("startup")
async def startup_event():
    global chunker, classifier, aggregator
    chunker = SentenceChunker(min_length=settings.min_sentence_length)
    classifier = TherapyClassifier(
        model_name=settings.model_name,
        categories=settings.categories,
        device=settings.device
    )
    aggregator = ResultAggregator(categories=settings.categories)


@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Therapy Classification API",
        "endpoints": {
            "POST /classify": "Classify therapy text",
            "GET /health": "Health check",
            "GET /categories": "List available categories"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        model=settings.model_name,
        device=settings.device
    )


@app.get("/categories", response_model=CategoriesResponse)
async def get_categories():
    return CategoriesResponse(categories=settings.categories)


@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    try:
        sentences = chunker.chunk(request.text)

        if not sentences:
            raise HTTPException(
                status_code=400,
                detail="No valid sentences found in the provided text"
            )

        classifications = classifier.classify_batch(sentences)

        aggregated_results = aggregator.aggregate(classifications)

        return ClassificationResponse(categories=aggregated_results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

