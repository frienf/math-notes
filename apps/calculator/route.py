from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import base64
import re
from apps.calculator.utils import analyze_image, validate_image
from schema import ImageData
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("")
async def run(data: ImageData):
    try:
        # Validate and decode the base64 image
        match = re.match(r"data:image/(png|jpeg);base64,(.+)", data.image)
        if not match:
            logger.error("Invalid image format: %s", data.image[:50])
            raise HTTPException(
                status_code=400,
                detail="Invalid image format. Expected data:image/(png|jpeg);base64,..."
            )
        
        image_data = base64.b64decode(match.group(2))
        
        # Validate the image
        image = validate_image(image_data)
        
        try:
            # Analyze the image
            logger.info("Analyzing image with variables: %s", data.dict_of_vars)
            response = analyze_image(image, dict_of_vars=data.dict_of_vars)
            
            # Check for errors
            if response.get("error"):
                logger.error("Image analysis failed: %s", response["error"])
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": response["error"],
                        "data": [],
                        "status": "error"
                    }
                )
            
            # Process successful responses
            data_list = response.get("result", [])
            if not isinstance(data_list, list):
                logger.error("Invalid data_list format: %s", data_list)
                raise ValueError("Response result is not a list")
            
            for item in data_list:
                if not isinstance(item, dict) or "expr" not in item or "result" not in item:
                    logger.error("Invalid response item: %s", item)
                    raise ValueError("Invalid response item format")
                logger.debug("Processed response: %s", str(item))  # Explicit str() to avoid format issues
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Image processed",
                    "data": data_list,
                    "status": "success"
                }
            )
        finally:
            image.close()
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Internal server error: %s, data: %s", str(e), data.image[:50])
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Internal server error: {str(e)}",
                "data": [],
                "status": "error"
            }
        )