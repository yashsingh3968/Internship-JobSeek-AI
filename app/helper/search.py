# Import Pydantic's BaseModel so response/request objects can be validated.
from pydantic import BaseModel

# Import typing helpers used by the schema fields below.
from typing import Optional, List


# Define the shape of one job listing returned by the scraper.
class JobListing(BaseModel):
    # Store the job title shown to the user.
    title: str
    # Store the company or employer name.
    company: str
    # Store the human-readable job location.
    location: str
    # Store a short job description snippet, defaulting to an empty string.
    description: Optional[str] = ""
    # Store the apply URL for the job.
    url: str
    # Store the source name, such as "indeed" or "linkedin".
    source: str


# Define the JSON body expected by the manual job search endpoint.
class SearchRequest(BaseModel):
    # Store the user's search keywords.
    query: str
    # Store the target location, defaulting to India.
    location: Optional[str] = "India"
    # Store the maximum number of results requested.
    max_results: Optional[int] = 20


# Define the structured resume analysis returned by Gemini.
class ResumeAnalysisResponse(BaseModel):
    # Store extracted resume keywords.
    keywords: List[str]
    # Store suggested job roles for the candidate.
    suggested_roles: List[str]
    # Store the concise resume summary.
    skills_summary: str


# Define the full job search response returned by the API.
class JobSearchResponse(BaseModel):
    # Store the number of raw listings found before deduplication.
    total_found: int
    # Store the number of listings left after deduplication.
    deduplicated_count: int
    # Store the final list of job listings.
    jobs: List[JobListing]
