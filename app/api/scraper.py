# Import asyncio so multiple job-source requests can run concurrently.
import asyncio

# Import aiohttp for async HTTP requests to the job search API.
import aiohttp

# Import List for typed job collections.
from typing import List

# Import the shared job listing model.
from helper.search import JobListing


# Store the RapidAPI key used by the JSearch API.
JSEARCH_API_KEY = "553b20b768msh2f6a720204ad209p175c0ejsn3cf02639fd80"

# Store the RapidAPI host for the JSearch API.
JSEARCH_HOST = "jsearch.p.rapidapi.com"


# Fetch and combine jobs from configured job publishers.
class JobAggregator:
    # Build HTTP headers required by RapidAPI.
    def _build_headers(self) -> dict:
        # Return the authentication and host headers.
        return {
            # Send the API key to RapidAPI.
            "X-RapidAPI-Key": JSEARCH_API_KEY,
            # Tell RapidAPI which hosted API is being called.
            "X-RapidAPI-Host": JSEARCH_HOST,
        }

    # Fetch jobs for one source filter, such as Indeed or LinkedIn.
    async def _fetch_from_source(
        # Keep a reference to the aggregator instance.
        self,
        # Reuse the shared aiohttp session.
        session: aiohttp.ClientSession,
        # Use the generated or user-entered search query.
        query: str,
        # Search within the requested location.
        location: str,
        # Filter API results by publisher name.
        source_filter: str,
        # Limit results per source.
        max_results: int,
    ) -> List[JobListing]:
        # Build the JSearch endpoint URL.
        url = f"https://{JSEARCH_HOST}/search"
        # Build query parameters sent to JSearch.
        params = {
            # Combine role keywords and location into one search phrase.
            "query": f"{query} in {location}",
            # Read the first results page.
            "page": "1",
            # Limit API pagination to a single page.
            "num_pages": "1",
            # Prefer jobs posted within the last month.
            "date_posted": "month",
        }
        # Prepare a list for successfully parsed jobs.
        jobs: List[JobListing] = []
        # Log the outbound source fetch.
        print(f"[JobAggregator] Fetching {source_filter} jobs for '{query}' in {location}")
        # Catch source-specific failures so one source does not crash the whole search.
        try:
            # Send the GET request to the external job API.
            async with session.get(url, headers=self._build_headers(), params=params) as resp:
                # Log the HTTP status for debugging.
                print(f"[JobAggregator] {source_filter} response status: {resp.status}")
                # Return an empty list if the API call failed.
                if resp.status != 200:
                    # Leave the source empty on non-success responses.
                    return jobs
                # Decode the API response body as JSON.
                data = await resp.json()
                # Read the list of raw job records from the response.
                raw_jobs = data.get("data", [])
                # Iterate over the requested number of raw jobs.
                for job in raw_jobs[:max_results]:
                    # Read the employer name with a safe fallback.
                    employer = job.get("employer_name", "Unknown Company")
                    # Read the job city with a safe fallback.
                    city = job.get("job_city", "")
                    # Read the job state with a safe fallback.
                    state = job.get("job_state", "")
                    # Build a readable location string.
                    location_str = f"{city}, {state}".strip(", ") or location
                    # Read the application link with a fallback.
                    apply_link = job.get("job_apply_link", "#")
                    # Normalize the publisher name for filtering.
                    publisher = job.get("job_publisher", "").lower()
                    # Skip this record if it does not match the requested source.
                    if source_filter and source_filter not in publisher:
                        # Continue to the next raw job.
                        continue
                    # Convert the raw API record into the app's JobListing model.
                    jobs.append(
                        JobListing(
                            # Copy the job title.
                            title=job.get("job_title", "N/A"),
                            # Copy the employer name.
                            company=employer,
                            # Copy the formatted location.
                            location=location_str,
                            # Keep the description short for UI display.
                            description=job.get("job_description", "")[:300],
                            # Copy the apply URL.
                            url=apply_link,
                            # Store the source name.
                            source=source_filter or publisher,
                        )
                    )
        # Swallow source-specific errors and log them for debugging.
        except Exception as exc:
            # Print the source failure without crashing the full search.
            print(f"[JobAggregator] {source_filter} fetch failed: {exc}")
        # Log how many jobs this source produced.
        print(f"[JobAggregator] {source_filter} returned {len(jobs)} filtered jobs")
        # Return the parsed jobs for this source.
        return jobs

    # Fetch jobs from all configured sources at the same time.
    async def fetch_all(self, query: str, location: str = "India", max_results: int = 20) -> List[JobListing]:
        # Log the start of the aggregate search.
        print(f"[JobAggregator] Starting aggregate search for '{query}'")
        # Create one HTTP session for all source requests.
        async with aiohttp.ClientSession() as session:
            # Create the Indeed fetch coroutine.
            indeed_task = self._fetch_from_source(session, query, location, "indeed", max_results)
            # Create the LinkedIn fetch coroutine.
            linkedin_task = self._fetch_from_source(session, query, location, "linkedin", max_results)
            # Await both source fetches concurrently.
            results = await asyncio.gather(indeed_task, linkedin_task)
        # Prepare a single combined job list.
        all_jobs: List[JobListing] = []
        # Flatten each source batch into the combined list.
        for batch in results:
            # Add this source batch to the aggregate output.
            all_jobs.extend(batch)
        # Log the final raw job count.
        print(f"[JobAggregator] Aggregate search returned {len(all_jobs)} jobs")
        # Return the combined job list.
        return all_jobs

    # Provide a sync wrapper for scripts that are not already inside an event loop.
    def fetch_jobs_sync(self, query: str, location: str = "India", max_results: int = 20) -> List[JobListing]:
        # Log sync wrapper usage.
        print("[JobAggregator] Running async fetch through sync wrapper")
        # Run the async fetch in a new event loop.
        return asyncio.run(self.fetch_all(query, location, max_results))
