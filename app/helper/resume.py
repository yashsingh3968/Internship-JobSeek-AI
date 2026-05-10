# Import PyPDF2 so PDF resumes can be read.
import PyPDF2

# Import python-docx so DOCX resumes can be read.
import docx

# Import io so uploaded bytes can be treated like file objects.
import io

# Import UploadFile for FastAPI upload type hints.
from fastapi import UploadFile


# Parse resume uploads into plain text.
class ResumeParser:
    # Extract text from uploaded PDF bytes.
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        # Log the parser branch being used.
        print("[ResumeParser] Extracting text from PDF")
        # Accumulate text from all PDF pages.
        text = ""
        # Catch PDF parsing failures and convert them into user-facing errors.
        try:
            # Build a PDF reader from the in-memory upload bytes.
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            # Visit each page in the uploaded PDF.
            for page in reader.pages:
                # Extract text from the current page.
                extracted = page.extract_text()
                # Append text only when the page contains readable content.
                if extracted:
                    # Keep page text separated by newlines.
                    text += extracted + "\n"
        # Convert any low-level PDF error into a clean ValueError.
        except Exception as e:
            # Raise a clear parsing error for the API layer.
            raise ValueError(f"Failed to parse PDF: {str(e)}")
        # Log how much text was extracted.
        print(f"[ResumeParser] Extracted {len(text.strip())} characters from PDF")
        # Return trimmed resume text.
        return text.strip()

    # Extract text from uploaded DOCX bytes.
    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        # Log the parser branch being used.
        print("[ResumeParser] Extracting text from DOCX")
        # Accumulate text from all DOCX paragraphs.
        text = ""
        # Catch DOCX parsing failures and convert them into user-facing errors.
        try:
            # Build a DOCX document from the in-memory upload bytes.
            doc = docx.Document(io.BytesIO(file_bytes))
            # Collect non-empty paragraphs from the document.
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            # Join paragraphs with newlines to preserve readable structure.
            text = "\n".join(paragraphs)
        # Convert any low-level DOCX error into a clean ValueError.
        except Exception as e:
            # Raise a clear parsing error for the API layer.
            raise ValueError(f"Failed to parse DOCX: {str(e)}")
        # Log how much text was extracted.
        print(f"[ResumeParser] Extracted {len(text.strip())} characters from DOCX")
        # Return trimmed resume text.
        return text.strip()

    # Detect the uploaded resume type and parse it into text.
    async def parse(self, file: UploadFile) -> str:
        # Log the uploaded filename for debugging.
        print(f"[ResumeParser] Parsing uploaded file: {file.filename}")
        # Read all uploaded bytes from FastAPI's async file object.
        file_bytes = await file.read()
        # Normalize the filename before checking its extension.
        filename = file.filename.lower()
        # Parse as PDF when the extension or content type says PDF.
        if filename.endswith(".pdf") or file.content_type == "application/pdf":
            # Return parsed PDF text.
            return self.extract_text_from_pdf(file_bytes)
        # Parse as DOCX when the extension or content type says Word.
        elif filename.endswith(".docx") or "word" in (file.content_type or ""):
            # Return parsed DOCX text.
            return self.extract_text_from_docx(file_bytes)
        # Reject unsupported file types.
        else:
            # Raise a clear validation error for callers.
            raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")
