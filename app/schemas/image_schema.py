from pydantic import BaseModel

# User से क्या इनपुट चाहिए
class ImageRequest(BaseModel):
    prompt: str

# API क्या वापस भेजेगी (Response)
class ImageResponse(BaseModel):
    status: str
    image_url: str
