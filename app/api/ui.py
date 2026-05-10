# Import Streamlit for the browser-based user interface.
import streamlit as st

# Import requests so the UI can call the FastAPI backend.
import requests


# Store the FastAPI backend base URL.
API_BASE = "http://127.0.0.1:8000"


# Configure the Streamlit page title, icon, and layout.
st.set_page_config(page_title="JobSeek AI", page_icon="briefcase", layout="wide")

# Render the main app title.
st.title("JobSeek AI")

# Render the short product caption.
st.caption("AI-powered job search powered by Gemini and FastAPI")


# Send a POST request to the FastAPI backend with consistent error handling.
def api_post(path, **kwargs):
    # Log the outbound UI-to-API request.
    print(f"[Streamlit UI] POST {path}")
    # Convert request errors into Streamlit messages instead of app crashes.
    try:
        # Send the POST request with a timeout so the UI does not hang forever.
        return requests.post(f"{API_BASE}{path}", timeout=60, **kwargs)
    # Handle the case where the FastAPI server is not running.
    except requests.exceptions.ConnectionError:
        # Show a friendly backend-down message in the UI.
        st.error("FastAPI server is not running on http://127.0.0.1:8000")
        # Show the command needed to start the backend.
        st.code(".\\.venv\\Scripts\\uvicorn.exe main:app --reload --port 8000", language="powershell")
    # Handle slow or stuck backend requests.
    except requests.exceptions.Timeout:
        # Show a timeout message in the UI.
        st.error("The API request timed out. Please try again.")
    # Handle any other requests-level error.
    except requests.exceptions.RequestException as exc:
        # Show the request exception in the UI.
        st.error(f"API request failed: {exc}")
    # Return None when the request did not complete successfully.
    return None


# Render a useful error message from a non-200 API response.
def show_api_error(resp, fallback):
    # Try to read FastAPI's JSON error format.
    try:
        # Use FastAPI's "detail" field when available.
        detail = resp.json().get("detail", fallback)
    # Fall back to raw text if the response is not JSON.
    except ValueError:
        # Prefer response text, otherwise use the fallback message.
        detail = resp.text or fallback
    # Show the final error message in Streamlit.
    st.error(detail)


# Render the job search result payload returned by the API.
def display_job_results(data):
    # Guard against unexpected response shapes.
    if not data or "jobs" not in data:
        # Show a clear error when the result format is wrong.
        st.error("The API returned an unexpected job-results format.")
        # Render the raw payload to make debugging easier.
        st.json(data)
        # Stop rendering this result block.
        return

    # Log the result count for terminal debugging.
    print(f"[Streamlit UI] Displaying {len(data['jobs'])} jobs")
    # Show a summary count above the results.
    st.success(f"Found **{data['total_found']}** listings -> **{data['deduplicated_count']}** after deduplication")
    # Render each job inside an expandable section.
    for job in data["jobs"]:
        # Use the title and company as the expander label.
        with st.expander(f"**{job['title']}** - {job['company']}"):
            # Split metadata and apply link into two columns.
            col_a, col_b = st.columns([3, 1])
            # Render the job metadata in the wider column.
            with col_a:
                # Show location and source.
                st.write(f"Location: {job['location']} | Source: `{job['source']}`")
            # Render the application link in the narrow column.
            with col_b:
                # Show a clickable apply link.
                st.markdown(f"[Apply Now]({job['url']})")
            # Show the description only when one exists.
            if job.get("description"):
                # Render the description in an info block.
                st.info(job["description"])


# Create the three primary app tabs.
tab1, tab2, tab3 = st.tabs(["Resume Analysis", "Manual Search", "Auto-Match Jobs"])


# Render the resume analysis tab.
with tab1:
    # Render the tab heading.
    st.header("Resume Insights")
    # Render a short instruction.
    st.write("Upload a resume to extract core competencies and suggested career paths.")

    # Create the resume upload control.
    up_file = st.file_uploader("Upload PDF/DOCX", type=["pdf", "docx"], key="tab1_upload")

    # Run analysis only after a file is uploaded and the button is clicked.
    if up_file and st.button("Analyze Resume", type="primary", key="tab1_btn"):
        # Show a spinner while the backend processes the resume.
        with st.spinner("Gemini is dissecting the resume..."):
            # Send the uploaded file to the resume-analysis endpoint.
            resp = api_post(
                # Call the resume-analysis route.
                "/analyze-resume",
                # Send the uploaded file as multipart form data.
                files={"file": (up_file.name, up_file.getvalue(), up_file.type)},
            )

        # Render analysis results when the API call succeeds.
        if resp and resp.status_code == 200:
            # Decode the JSON response.
            analysis = resp.json()
            # Store keywords so the manual search tab can reuse them.
            st.session_state["keywords"] = analysis["keywords"]

            # Create two columns for the analysis output.
            c1, c2 = st.columns(2)
            # Render keywords and suggested roles in the left column.
            with c1:
                # Render the key skills heading.
                st.subheader("Key Skills")
                # Render keywords as inline code chips.
                st.write(", ".join([f"`{k}`" for k in analysis["keywords"]]))

                # Render suggested roles heading.
                st.subheader("Suggested Roles")
                # Render each suggested role as a bullet.
                for role in analysis["suggested_roles"]:
                    # Write one role per line.
                    st.write(f"- {role}")

            # Render summary in the right column.
            with c2:
                # Render summary heading.
                st.subheader("Executive Summary")
                # Render summary content.
                st.info(analysis["skills_summary"])
        # Render API errors when the request completed but failed.
        elif resp:
            # Show the backend error detail.
            show_api_error(resp, "Failed to analyze resume.")


# Render the manual search tab.
with tab2:
    # Render the tab heading.
    st.header("Custom Job Search")

    # Create side-by-side query and location inputs.
    col1, col2 = st.columns([3, 1])
    # Render the keyword input in the wider column.
    with col1:
        # Load keywords saved from the resume-analysis tab.
        kw_list = st.session_state.get("keywords", [])
        # Build a default query from the first three keywords.
        default_q = " ".join(kw_list[:3]) if kw_list else ""
        # Render the search keyword input.
        query = st.text_input("Search Keywords", value=default_q, placeholder="e.g. Java Lead, MLOps Engineer")
    # Render the location input in the narrower column.
    with col2:
        # Render the target location input.
        location = st.text_input("Location", value="India")

    # Render the result-limit slider.
    max_res = st.slider("Results per Source", 5, 50, 20)

    # Run manual search when the button is clicked.
    if st.button("Search Jobs", type="primary"):
        # Require a non-empty search query.
        if not query.strip():
            # Warn the user when no query is available.
            st.warning("Enter a query or analyze a resume first.")
        # Call the API when the query is valid.
        else:
            # Show a spinner while searching.
            with st.spinner("Searching..."):
                # Send search parameters as JSON.
                resp = api_post(
                    # Call the manual job-search route.
                    "/search-jobs",
                    # Send query, location, and max result count.
                    json={"query": query, "location": location, "max_results": max_res},
                )
                # Render results when the API call succeeds.
                if resp and resp.status_code == 200:
                    # Display the response payload.
                    display_job_results(resp.json())
                # Render API errors when the request completed but failed.
                elif resp:
                    # Show the backend error detail.
                    show_api_error(resp, "Job search failed.")


# Render the combined resume-to-jobs tab.
with tab3:
    # Render the tab heading.
    st.header("Instant Match")
    # Render a short instruction.
    st.write("One-click: Analyze resume and fetch matching jobs immediately.")

    # Create the resume upload control for auto-match.
    auto_file = st.file_uploader("Upload Resume", type=["pdf", "docx"], key="tab3_upload")

    # Create side-by-side location and limit inputs.
    ac1, ac2 = st.columns(2)
    # Render preferred location input.
    with ac1:
        # Store the preferred location.
        auto_loc = st.text_input("Preferred Location", value="India", key="tab3_loc")
    # Render max result input.
    with ac2:
        # Store the max result count.
        auto_max = st.number_input("Max Results", 5, 100, 20, key="tab3_max")

    # Run the full pipeline when clicked.
    if st.button("Find My Matches", type="primary"):
        # Require a resume upload first.
        if not auto_file:
            # Show a missing-file error.
            st.error("Please upload a resume.")
        # Call the API when a resume is uploaded.
        else:
            # Show a spinner while the full pipeline runs.
            with st.spinner("Running end-to-end pipeline..."):
                # Send resume and options to the combined endpoint.
                resp = api_post(
                    # Call the resume-to-jobs route.
                    "/resume-to-jobs",
                    # Send the uploaded file as multipart form data.
                    files={"file": (auto_file.name, auto_file.getvalue(), auto_file.type)},
                    # Send scalar options as form fields.
                    data={"location": auto_loc, "max_results": auto_max},
                )
                # Render job results when the API call succeeds.
                if resp and resp.status_code == 200:
                    # Decode the combined response payload.
                    payload = resp.json()
                    # Display only the nested job-results object.
                    display_job_results(payload.get("job_results"))
                # Render API errors when the request completed but failed.
                elif resp:
                    # Show the backend error detail.
                    show_api_error(resp, "Auto-match failed. Check your API server.")
