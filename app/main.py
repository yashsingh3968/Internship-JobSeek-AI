# Import FastAPI primitives used to build the HTTP API.
from fastapi import FastAPI, UploadFile, File, HTTPException

# Import CORS middleware so browser clients can call the API.
from fastapi.middleware.cors import CORSMiddleware

# Import the application controller that coordinates business logic.
from controller import Controller

# Import request and response schemas used by routes.
from helper.search import SearchRequest, JobSearchResponse, ResumeAnalysisResponse


# Create the FastAPI application object.
app = FastAPI(
    # Set the API title shown in generated docs.
    title="JobSeek AI API",
    # Set the API description shown in generated docs.
    description="AI-powered job aggregation and resume analysis platform",
    # Set the API version shown in generated docs.
    version="1.0.0",
)

# Enable broad CORS access for frontend development.
app.add_middleware(
    # Use Starlette's CORS middleware.
    CORSMiddleware,
    # Allow all origins during development.
    allow_origins=["*"],
    # Allow all HTTP methods during development.
    allow_methods=["*"],
    # Allow all request headers during development.
    allow_headers=["*"],
)

# Create one controller instance for all requests.
controller = Controller()


# Register a lightweight health-check route.
@app.get("/health")
def health_check():
    # Log health checks so server activity is visible.
    print("[API] Health check requested")
    # Return a simple service status payload.
    return {"status": "ok", "service": "JobSeek AI"}


# Register the resume-analysis endpoint.
@app.post("/analyze-resume", response_model=ResumeAnalysisResponse)
async def analyze_resume(file: UploadFile = File(...)):
    # Log the endpoint call.
    print(f"[API] /analyze-resume called with file={file.filename}")
    # Reject unsupported file extensions before reading the upload.
    if not file.filename.endswith((".pdf", ".docx")):
        # Return a 400 response for unsupported upload types.
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    # Convert controller exceptions into HTTP responses.
    try:
        # Delegate resume processing to the controller.
        return await controller.process_resume(file)
    # Convert validation failures into unprocessable-entity responses.
    except ValueError as e:
        # Return a 422 response with the validation message.
        raise HTTPException(status_code=422, detail=str(e))
    # Convert Gemini/service failures into service-unavailable responses.
    except RuntimeError as e:
        # Return a 503 response with the service error.
        raise HTTPException(status_code=503, detail=str(e))


# Register the manual job-search endpoint.
@app.post("/search-jobs", response_model=JobSearchResponse)
async def search_jobs(request: SearchRequest):
    # Log the endpoint call.
    print(f"[API] /search-jobs called with query='{request.query}'")
    # Convert unexpected search failures into HTTP responses.
    try:
        # Delegate job search to the controller.
        return await controller.search_jobs(
            # Pass through the search query.
            query=request.query,
            # Pass through the requested location.
            location=request.location,
            # Pass through the requested result limit.
            max_results=request.max_results,
        )
    # Convert unexpected failures into internal-server-error responses.
    except Exception as e:
        # Return a 500 response with the error details.
        raise HTTPException(status_code=500, detail=str(e))


# Register the combined resume-to-jobs endpoint.
@app.post("/resume-to-jobs")
async def resume_to_jobs(file: UploadFile = File(...), location: str = "India", max_results: int = 20):
    # Log the endpoint call.
    print(f"[API] /resume-to-jobs called with file={file.filename}, location={location}")
    # Convert controller exceptions into HTTP responses.
    try:
        # Run the combined resume analysis and job search workflow.
        return await controller.resume_to_jobs(file, location, max_results)
    # Convert validation failures into unprocessable-entity responses.
    except ValueError as e:
        # Return a 422 response with the validation message.
        raise HTTPException(status_code=422, detail=str(e))
    # Convert unexpected failures into internal-server-error responses.
    except Exception as e:
        # Return a 500 response with the error details.
        raise HTTPException(status_code=500, detail=str(e))
