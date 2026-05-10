# Import the resume parser used for uploaded files.
from helper.resume import ResumeParser

# Import the Gemini wrapper used for resume analysis and query generation.
from helper.llm import GeminiModule

# Import the job aggregator used to fetch listings.
from api.scraper import JobAggregator

# Import the deduper used to remove duplicate listings.
from api.deduper import Deduper

# Import shared response models.
from helper.search import JobSearchResponse, ResumeAnalysisResponse

# Import UploadFile for FastAPI upload type hints.
from fastapi import UploadFile

# Import Optional for nullable/defaulted arguments.
from typing import Optional


# Coordinate parser, LLM, scraper, and deduper workflows.
class Controller:
    # Initialize reusable service objects.
    def __init__(self):
        # Log controller startup.
        print("[Controller] Initializing services")
        # Create the resume parser.
        self.parser = ResumeParser()
        # Create the Gemini integration.
        self.gemini = GeminiModule()
        # Create the job aggregator.
        self.aggregator = JobAggregator()
        # Create the deduper.
        self.deduper = Deduper()

    # Parse and analyze one uploaded resume.
    async def process_resume(self, file: UploadFile) -> ResumeAnalysisResponse:
        # Log the resume-processing workflow start.
        print("[Controller] Processing resume")
        # Extract plain text from the uploaded resume.
        resume_text = await self.parser.parse(file)
        # Reject resumes when no text could be extracted.
        if not resume_text:
            # Raise a validation error for FastAPI to return.
            raise ValueError("Could not extract text from the uploaded file.")
        # Send extracted text to Gemini for structured analysis.
        analysis = self.gemini.analyze_resume(resume_text)
        # Log successful analysis completion.
        print("[Controller] Resume analysis complete")
        # Return the structured analysis.
        return analysis

    # Search jobs for a query and return deduplicated results.
    async def search_jobs(self, query: str, location: str = "India", max_results: int = 20) -> JobSearchResponse:
        # Log the search request details.
        print(f"[Controller] Searching jobs: query='{query}', location='{location}', max_results={max_results}")
        # Fetch raw jobs from external sources.
        raw_jobs = await self.aggregator.fetch_all(query, location, max_results)
        # Deduplicate the raw jobs.
        clean_jobs = self.deduper.deduplicate(raw_jobs)
        # Calculate summary stats for the response.
        stats = self.deduper.get_dedup_stats(raw_jobs, clean_jobs)
        # Log the final job-search result count.
        print(f"[Controller] Job search complete: {stats['deduplicated_count']} unique jobs")
        # Return the public API response model.
        return JobSearchResponse(
            # Include the raw job count.
            total_found=stats["original_count"],
            # Include the deduplicated job count.
            deduplicated_count=stats["deduplicated_count"],
            # Include the final job list.
            jobs=clean_jobs,
        )

    # Analyze a resume and immediately search matching jobs.
    async def resume_to_jobs(self, file: UploadFile, location: Optional[str] = "India", max_results: int = 20) -> dict:
        # Log the combined pipeline start.
        print("[Controller] Starting resume-to-jobs pipeline")
        # Analyze the uploaded resume first.
        analysis = await self.process_resume(file)
        # Generate search keywords from the resume analysis.
        search_query = self.gemini.generate_search_query(analysis.keywords, location)
        # Search jobs using the generated query.
        job_results = await self.search_jobs(search_query, location, max_results)
        # Log the combined pipeline completion.
        print("[Controller] Resume-to-jobs pipeline complete")
        # Return both resume analysis and job results.
        return {
            # Include the structured resume analysis.
            "resume_analysis": analysis,
            # Include the query used for transparency.
            "search_query_used": search_query,
            # Include deduplicated job search results.
            "job_results": job_results,
        }
