from pydantic import BaseModel, validator
import base64
import re

class ImageData(BaseModel):
    image: str
    dict_of_vars: dict

    @validator("image")
    def validate_image(cls, value):
        # Check if it's a valid base64 string with data URI prefix
        pattern = r"^data:image/(png|jpeg);base64,[A-Za-z0-9+/=]+$"
        if not re.match(pattern, value):
            raise ValueError("Invalid base64 image data")
        try:
            base64.b64decode(value.split(",")[1])
        except Exception:
            raise ValueError("Failed to decode base64 image")
        return value