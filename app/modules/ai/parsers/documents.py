import io
from pathlib import Path
from typing import Union

def parse_pdf(content: bytes) -> str:
    import fitz  # PyMuPDF
    MAX_PAGES = 30
    doc = fitz.open(stream=content, filetype="pdf")
    if doc.page_count > MAX_PAGES:
        raise ValueError(f"PDF too large: {doc.page_count} pages. Maximum is {MAX_PAGES} pages.")
    text = "\n".join(page.get_text() for page in doc).strip()
    if not text:
        # Scanned PDF — render pages as images and extract via VLM
        import base64
        from langchain_core.messages import HumanMessage
        from app.modules.ai.llm import get_llm
        llm = get_llm()
        pages_text = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            response = llm.invoke([HumanMessage(content=[
                {"type": "text", "text": "Extract all text from this page exactly as it appears. Return only the text."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ])])
            pages_text.append(response.content)
        return "\n\n".join(pages_text)
    return text

def parse_image(content: bytes) -> str:
    import base64
    from langchain_core.messages import HumanMessage
    from app.modules.ai.llm import get_llm

    # Detect MIME type from magic bytes
    if content[:8] == b'\x89PNG\r\n\x1a\n':
        mime = "image/png"
    elif content[:2] == b'\xff\xd8':
        mime = "image/jpeg"
    elif content[8:12] == b'WEBP':
        mime = "image/webp"
    elif content[:4] in (b'II*\x00', b'MM\x00*'):
        mime = "image/tiff"
    else:
        mime = "image/jpeg"

    b64 = base64.b64encode(content).decode("utf-8")
    llm = get_llm()
    message = HumanMessage(content=[
        {
            "type": "text",
            "text": (
                "Extract all text from this image exactly as it appears. "
                "Preserve the original structure and formatting. "
                "Return only the extracted text, no commentary or explanation."
            )
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"}
        }
    ])
    response = llm.invoke([message])
    return response.content

def parse_docx(content: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def parse_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")

def parse_file(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(content)
    elif suffix in (".png", ".jpg", ".jpeg", ".webp", ".tiff"):
        return parse_image(content)
    elif suffix == ".docx":
        return parse_docx(content)
    elif suffix in (".txt", ".md"):
        return parse_txt(content)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
