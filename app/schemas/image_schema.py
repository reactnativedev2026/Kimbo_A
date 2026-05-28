from pydantic import BaseModel

class ImageRequest(BaseModel):
    prompt: str

class ImageResponse(BaseModel):
    status: str
    image_url: str
