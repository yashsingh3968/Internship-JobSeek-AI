# Import the Google GenAI SDK used for Gemini calls.
from google import genai

# Import BaseModel so Gemini can validate structured JSON output.
from pydantic import BaseModel

# Import List for schema type hints.
from typing import List

# Import the shared response model returned to API callers.
from helper.search import ResumeAnalysisResponse


# Define the JSON schema Gemini should return.
class AnalysisSchema(BaseModel):
    # Store extracted resume keywords.
    keywords: List[str]
    # Store role suggestions inferred from the resume.
    suggested_roles: List[str]
    # Store a concise recruiter-style summary.
    skills_summary: str


# Wrap Gemini resume-analysis and search-query behavior.
class GeminiModule:
    # Initialize the Gemini client once for reuse.
    def __init__(self):
        # Log SDK setup without printing the API key.
        print("[GeminiModule] Initializing Gemini client")
        # Create the Gemini API client with the configured key.
        self.client = genai.Client(api_key="AIzaSyBWpLIXTMKl8dqa7-Tsm6tLN6EwVKiizLc")
        # Store the model name used for resume analysis.
        self.model_id = "gemini-2.5-flash"

    # Analyze resume text and return structured career information.
    def analyze_resume(self, resume_text: str) -> ResumeAnalysisResponse:
        # Log the size of the prompt input for debugging.
        print(f"[GeminiModule] Analyzing resume text with {len(resume_text)} characters")
        # Build the recruiter-style instruction prompt.
        prompt = f"""
        You are an expert technical recruiter and resume analyst.
        Analyze the following resume text and extract the required information.

        Resume Text:
        \"\"\"
        {resume_text}
        \"\"\"
        """

        # Convert Gemini or network failures into a RuntimeError for the API layer.
        try:
            # Ask Gemini for schema-constrained JSON.
            response = self.client.models.generate_content(
                # Select the configured Gemini model.
                model=self.model_id,
                # Send the prompt as the request content.
                contents=prompt,
                # Configure Gemini to return structured JSON matching AnalysisSchema.
                config={
                    # Request a JSON response body.
                    "response_mime_type": "application/json",
                    # Ask the SDK to parse the response into this schema.
                    "response_schema": AnalysisSchema,
                },
            )

            # Read the parsed schema object returned by the SDK.
            data = response.parsed
            # Log the number of extracted keywords.
            print(f"[GeminiModule] Gemini returned {len(data.keywords)} keywords")

            # Convert the parsed SDK schema into the app's public response model.
            return ResumeAnalysisResponse(
                # Copy extracted keywords into the response.
                keywords=data.keywords,
                # Copy suggested roles into the response.
                suggested_roles=data.suggested_roles,
                # Copy the skills summary into the response.
                skills_summary=data.skills_summary,
            )

        # Surface Gemini failures as service errors.
        except Exception as e:
            # Raise a consistent runtime error for FastAPI to translate.
            raise RuntimeError(f"Gemini API error: {str(e)}")

    # Build a compact job search query from resume keywords.
    def generate_search_query(self, keywords: list, location: str = "India") -> str:
        # Log query generation inputs.
        print(f"[GeminiModule] Generating search query for {len(keywords)} keywords in {location}")
        # Keep only the first three keywords so the search query stays focused.
        top_keywords = keywords[:3] if len(keywords) >= 3 else keywords
        # Join the selected keywords into a plain search query.
        query = " ".join(top_keywords)
        # Log the final query.
        print(f"[GeminiModule] Search query: {query}")
        # Return the generated query.
        return query
