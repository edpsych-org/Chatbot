"""
File Upload API Routes
IQ test uploads and processing
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/iq-test")
async def upload_iq_test():
    """Upload an IQ test file (PDF/image)"""
    return {"message": "Upload IQ test endpoint - to be implemented"}


@router.get("/{upload_id}")
async def get_upload_status(upload_id: str):
    """Get upload processing status"""
    return {"message": f"Get upload {upload_id} status - to be implemented"}


@router.post("/{upload_id}/process")
async def process_upload(upload_id: str):
    """Trigger OCR processing for an upload"""
    return {"message": f"Process upload {upload_id} - to be implemented"}
