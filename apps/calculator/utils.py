import requests
import json
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import base64
from constants import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MAX_IMAGE_PIXELS, ALLOWED_IMAGE_FORMATS
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def validate_image(image_data: bytes, max_pixels: int = MAX_IMAGE_PIXELS, allowed_formats: tuple = ALLOWED_IMAGE_FORMATS) -> Image.Image:
    try:
        logger.debug("Validating image of size %d bytes", len(image_data))
        img = Image.open(BytesIO(image_data))
        if img.format not in allowed_formats:
            logger.error("Unsupported image format: %s", img.format)
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format: {img.format}. Allowed formats: {', '.join(allowed_formats)}"
            )
        if img.size[0] * img.size[1] > max_pixels:
            logger.error("Image too large: %dx%d pixels", img.size[0], img.size[1])
            raise HTTPException(
                status_code=400,
                detail=f"Image is too large: {img.size[0]}x{img.size[1]} pixels exceeds {max_pixels:,} pixel limit"
            )
        logger.info("Image validated successfully: %dx%d, format: %s", img.size[0], img.size[1], img.format)
        return img
    except UnidentifiedImageError:
        logger.error("Invalid image data: Unable to identify image format")
        raise HTTPException(status_code=400, detail="Invalid image: Unable to identify image format")
    except Exception as e:
        logger.error("Unexpected error validating image: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

def analyze_image(img: Image, dict_of_vars: dict):
    dict_of_vars_str = json.dumps(dict_of_vars, ensure_ascii=False)
    prompt = (
        f"Analyze the mathematical content in the image and return a JSON string containing a list of dictionaries. "
        f"Supported cases: "
        f"1. Simple expressions (e.g., '2 + 2'): Return [{{'expr': '2 + 2', 'result': 4}}]. "
        f"2. Equations (e.g., 'x^2 + 2x + 1 = 0'): Return [{{'expr': 'x', 'result': -1, 'assign': true}}]. "
        f"3. Variable assignments (e.g., 'x = 4'): Return [{{'expr': 'x', 'result': 4, 'assign': true}}]. "
        f"4. Graphical problems (e.g., Pythagorean theorem): Return [{{'expr': 'a^2 + b^2 = c^2', 'result': 5}}]. "
        f"5. Abstract concepts (e.g., a heart): Return [{{'expr': 'A heart symbol', 'result': 'love'}}]. "
        f"Use PEMDAS for calculations. If variables are used, refer to this dictionary: {dict_of_vars_str}. "
        f"Escape special characters (e.g., '\\n' as '\\\\n'). "
        f"Return only the JSON string, without markdown, backticks, or additional text."
    )
    try:
        # Compress image to reduce size
        max_size = (512, 512)  # Smaller size to reduce tokens
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert image to base64
        buffered = BytesIO()
        img.save(buffered, format=img.format, quality=75)  # Lower quality
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        img_mime = f"image/{img.format.lower()}"

        # Estimate token usage (rough: 1 token ~ 4 chars, image ~ 1000-2000 tokens)
        prompt_tokens = len(prompt) // 4 + 1000  # Approx image tokens
        logger.info("Estimated prompt tokens: %d (text: %d, image: ~1000)", prompt_tokens, len(prompt) // 4)

        # Prepare OpenRouter API request
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8900",
            "X-Title": "Predystopic Calculator"
        }
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{img_mime};base64,{img_base64}"}}
                    ]
                }
            ],
            "max_tokens": 2000  # Conservative limit
        }

        # Try multiple models
        models = ["x-ai/grok-2-vision-1212", "meta-llama/llama-4-maverick:free"]
        for model in models:
            payload["model"] = model
            logger.info("Sending image to OpenRouter API with model: %s", model)
            try:
                response = requests.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                response_data = response.json()

                # Check for error in response body
                if "error" in response_data:
                    logger.warning("API returned error for model %s: %s", model, response_data["error"])
                    if model == models[-1]:
                        return {"error": f"OpenRouter API error: {response_data['error']}", "result": []}
                    continue

                # Check for choices
                if "choices" not in response_data:
                    logger.error("No 'choices' in response for model %s: %s", model, response_data)
                    if model == models[-1]:
                        return {"error": "No 'choices' in OpenRouter API response", "result": []}
                    continue

                break
            except requests.HTTPError as e:
                try:
                    error_details = e.response.json()
                    logger.warning("HTTP error with model %s: %s", model, error_details)
                    if model == models[-1]:
                        raise
                    continue
                except ValueError:
                    logger.warning("HTTP error with model %s, no JSON details: %s", model, str(e))
                    if model == models[-1]:
                        raise
                    continue

        # Process response
        response_text = response_data["choices"][0]["message"]["content"].strip()

        # Preprocess to handle markdown or extra text
        if response_text.startswith("```json") and response_text.endswith("```"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text[3:-3].strip()

        logger.debug("Raw OpenRouter response: %s", response_text[:100])
        answers = json.loads(response_text)

        if not isinstance(answers, list):
            logger.error("Invalid response format: %s", response_text[:100])
            return {"error": "Invalid response format from OpenRouter API", "result": []}

        for answer in answers:
            if not isinstance(answer, dict) or "expr" not in answer or "result" not in answer:
                logger.error("Invalid answer format: %s", answer)
                return {"error": "Invalid answer format from OpenRouter API", "result": []}
            answer["assign"] = answer.get("assign", False)

        logger.info("Successfully analyzed image with %d responses", len(answers))
        return {"result": answers, "error": None}

    except requests.HTTPError as e:
        try:
            error_details = e.response.json()
            logger.error("OpenRouter API error: %s, details: %s", str(e), error_details)
            return {"error": f"OpenRouter API error: {str(e)} - {error_details}", "result": []}
        except ValueError:
            logger.error("OpenRouter API error: %s, no JSON details available", str(e))
            return {"error": f"OpenRouter API error: {str(e)}", "result": []}
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error in OpenRouter API response: %s, response: %s", str(e), response_text[:100])
        return {"error": f"Failed to parse OpenRouter API response: {str(e)}", "result": []}
    except requests.RequestException as e:
        logger.error("OpenRouter API request error: %s", str(e))
        return {"error": f"OpenRouter API request error: {str(e)}", "result": []}
    except Exception as e:
        logger.error("Unexpected error analyzing image: %s", str(e))
        return {"error": f"Failed to analyze image: {str(e)}", "result": []}