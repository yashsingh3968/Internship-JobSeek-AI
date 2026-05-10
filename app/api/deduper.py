# Import fuzzy matching so similar job titles can be compared.
from thefuzz import fuzz

# Import List for typed job collections.
from typing import List

# Import the shared job listing model.
from helper.search import JobListing


# Set the similarity score needed to treat two jobs as duplicates.
SIMILARITY_THRESHOLD = 95


# Encapsulate job deduplication behavior.
class Deduper:
    # Build a normalized text key for comparing one job with another.
    def _make_fingerprint(self, job: JobListing) -> str:
        # Combine title and company because that pair usually identifies a listing.
        return f"{job.title.lower().strip()} {job.company.lower().strip()}"

    # Remove near-duplicate job listings from a raw job list.
    def deduplicate(self, jobs: List[JobListing]) -> List[JobListing]:
        # Log the deduplication start so the terminal shows pipeline progress.
        print(f"[Deduper] Starting deduplication for {len(jobs)} jobs")
        # Store jobs that survive the duplicate check.
        unique_jobs: List[JobListing] = []
        # Store fingerprints for jobs already accepted.
        seen_fingerprints: List[str] = []
        # Check each scraped job one at a time.
        for job in jobs:
            # Create the comparable fingerprint for this job.
            fingerprint = self._make_fingerprint(job)
            # Assume the job is unique until a close match is found.
            is_duplicate = False
            # Compare this job with all previously accepted fingerprints.
            for seen in seen_fingerprints:
                # Mark as duplicate when the fuzzy score meets the threshold.
                if fuzz.token_sort_ratio(fingerprint, seen) >= SIMILARITY_THRESHOLD:
                    # Remember that this listing should not be added.
                    is_duplicate = True
                    # Stop comparing once a duplicate has been found.
                    break
            # Keep the job only when no duplicate was found.
            if not is_duplicate:
                # Add the unique job to the output list.
                unique_jobs.append(job)
                # Track its fingerprint for future comparisons.
                seen_fingerprints.append(fingerprint)
        # Log the final number of unique jobs.
        print(f"[Deduper] Finished with {len(unique_jobs)} unique jobs")
        # Return the deduplicated list.
        return unique_jobs

    # Calculate summary stats for the raw and deduplicated job lists.
    def get_dedup_stats(self, original: List[JobListing], deduplicated: List[JobListing]) -> dict:
        # Count how many records were removed.
        removed = len(original) - len(deduplicated)
        # Build a small stats dictionary for the API response.
        stats = {
            # Report the original raw count.
            "original_count": len(original),
            # Report the final unique count.
            "deduplicated_count": len(deduplicated),
            # Report the number of removed duplicate listings.
            "duplicates_removed": removed,
            # Report the percentage reduction, guarding against division by zero.
            "reduction_percent": round((removed / len(original)) * 100, 1) if original else 0,
        }
        # Log the deduplication summary.
        print(f"[Deduper] Stats: {stats}")
        # Return the computed stats.
        return stats
