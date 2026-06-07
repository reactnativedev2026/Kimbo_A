from typing import List, Annotated
from app.schemas.image_schema import ImageRequest, ImageResponse
from fastapi import APIRouter, UploadFile, File, HTTPException
import urllib.parse
import shutil
import os
import cloudinary
import cloudinary.uploader

router = APIRouter()

# Load environment variables (with override to support hot-reload of .env changes)
from dotenv import load_dotenv
load_dotenv(override=True)

# Configure Cloudinary
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "dsvb4n4lm"), 
    api_key = os.getenv("CLOUDINARY_API_KEY", "649237855112415"), 
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "yqpJpvlEgdSUiPv-5upl04Uhz5E"),
    secure = True
)

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
    try:
        # Extract filename without extension as public_id
        public_id = os.path.splitext(files.filename)[0]
        
        # Upload the file object to Cloudinary
        upload_result = cloudinary.uploader.upload(
            files.file,
            public_id=public_id
        )
        secure_url = upload_result.get("secure_url")
        
        return {
            "filename": files.filename,
            "content_type": files.content_type,
            "url": secure_url
        }
    except Exception as e:
        import logging
        logging.error(f"Error uploading image to Cloudinary: {e}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
@router.post("/uploadMultipleImage")
async def upload_image(
    files: Annotated[
        List[UploadFile], 
        File(description="Select multiple images")
    ]
):
    return {"files": files}

