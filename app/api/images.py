from typing import List, Annotated
from app.schemas.image_schema import ImageRequest, ImageResponse
from fastapi import APIRouter, UploadFile, File
import urllib.parse
import shutil
import os

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/generate", response_model=ImageResponse) # GET की जगह POST इस्तेमाल करना बेहतर है
def generate_image_api(request: ImageRequest):
    # Prompt को URL-friendly बनाएँ
    encoded_prompt = urllib.parse.quote(request.prompt)
    
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    
    return ImageResponse(
        status="success",
        image_url=image_url
    )

@router.post("/uploadImage")
async def upload_image(files: UploadFile = File(...)):
    # फ़ाइल का नाम और पाथ तय करें
    file_path = os.path.join(UPLOAD_DIR, files.filename)
    
    # फ़ाइल को सेव करें
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(files.file, buffer)
    
    # फ़ाइल का URL वापस भेजें (अभी local path भेज रहे हैं)
    return {
        "filename": files.filename,
        "content_type": files.content_type,
        "url": f"/static/{files.filename}" # Browser में देखने के लिए URL
    }
@router.post("/uploadMultipleImage")
async def upload_image(
    files: Annotated[
        List[UploadFile], 
        File(description="Select multiple images")
    ]
):
    return {"files": files}

