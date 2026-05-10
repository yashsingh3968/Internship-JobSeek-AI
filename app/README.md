# JobSeek AI — Code Files

## Project Structure
```
jobseek_ai/
├── main.py            # FastAPI application entry point
├── controller.py      # Orchestration controller
├── resume_parser.py   # PDF and DOCX text extraction
├── gemini_module.py   # Gemini LLM integration
├── job_aggregator.py  # Parallel job fetching (Indeed + LinkedIn)
├── deduper.py         # Fuzzy matching deduplication engine
├── models.py          # Pydantic data models
├── streamlit_app.py   # Streamlit frontend
└── requirements.txt   # Python dependencies
```

## Setup & Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your API keys in `gemini_module.py` and `job_aggregator.py`:
   - `YOUR_GEMINI_API_KEY` → Get from https://aistudio.google.com/
   - `YOUR_RAPIDAPI_KEY`   → Get from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

3. Start the FastAPI backend:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

4. In a separate terminal, start the Streamlit frontend:
   ```bash
   streamlit run streamlit_app.py
   ```

5. Open browser at: http://localhost:8501
