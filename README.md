# MathSketch Backend

frienf-math-notes-be is a FastAPI-based backend for the MathSketch application, designed to analyze mathematical expressions and graphical problems from images. It processes base64-encoded images sent from the frontend (frienf-math-notes-fe), validates them, and uses the OpenRouter API to evaluate expressions, equations, variable assignments, and graphical problems. The backend returns results in a structured JSON format, enabling the frontend to render LaTeX outputs.

## Features

-   **Image Processing:** Validates and processes base64-encoded PNG/JPEG images containing mathematical content.
-   **Expression Analysis:** Supports simple expressions (e.g., 2 + 2), equations (e.g., x^2 + 2x + 1 = 0), variable assignments (e.g., x = 4), graphical problems (e.g., Pythagorean theorem), and abstract concepts (e.g., heart symbol).
-   **OpenRouter Integration:** Uses vision-capable models (e.g., x-ai/grok-2-vision-1212) to analyze images and return structured results.
-   **Robust Validation:** Ensures images meet format and size requirements (e.g., max 10M pixels) using PIL.
-   **Logging:** Implements comprehensive logging for debugging and error tracking, with file and console outputs.
-   **CORS Support:** Configures CORS middleware for flexible frontend integration (restricted in production).
-   **Error Handling:** Provides detailed error responses for invalid inputs, API failures, or internal errors.

## Prerequisites

-   **Python:** Version 3.10 or higher.
-   **pip:** For installing dependencies.
-   **OpenRouter API Key:** Obtain from [OpenRouter](https://openrouter.ai/) for image analysis.
-   **Frontend:** A running instance of frienf-math-notes-fe (optional for testing).

## Setup

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/frienf/math-notes-be.git
    cd frienf-math-notes-be
    ```

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**

    *   Create a `.env` file in the root directory with the following:

        ```
        OPENROUTER_API_KEY=your_openrouter_api_key
        MAX_IMAGE_PIXELS=10000000
        ALLOWED_IMAGE_FORMATS=PNG,JPEG
        ```
    *   Replace `your_openrouter_api_key` with your OpenRouter API key.
    *   Adjust `MAX_IMAGE_PIXELS` or `ALLOWED_IMAGE_FORMATS` if needed.

4.  **Run the Development Server:**

    ```bash
    python main.py
    ```

    The server will start at `http://localhost:8900` in development mode with auto-reload.

## API Endpoints

### GET /

*   **Description:** Health check endpoint to verify the server is running.
*   **Response:**

    ```json
    {
      "message": "Server is running"
    }
    ```

### POST /calculate

*   **Description:** Analyzes a base64-encoded image containing mathematical content and returns evaluated results.
*   **Request Body:**

    ```json
    {
      "image": "data:image/png;base64,iVBORw0KGgo...",
      "dict_of_vars": {"x": "4", "y": "2"}
    }
    ```

    *   `image`: Base64-encoded PNG or JPEG image with a `data:image/(png|jpeg);base64,` prefix.
    *   `dict_of_vars`: Dictionary of variable assignments (optional).
*   **Response (Success):**

    ```json
    {
      "message": "Image processed",
      "data": [
        {"expr": "2 + 2", "result": "4", "assign": false},
        {"expr": "x", "result": "4", "assign": true}
      ],
      "status": "success"
    }
    ```
*   **Response (Error):**

    ```json
    {
      "message": "Invalid image format",
      "data": [],
      "status": "error"
    }
    ```
*   **Status Codes:**
    *   `200`: Successful processing.
    *   `400`: Invalid input (e.g., image format, size).
    *   `500`: Internal server error.

### POST /log-error

*   **Description:** Logs frontend errors for debugging.
*   **Request Body:**

    ```json
    {
      "error": "Description of the error"
    }
    ```
*   **Response:**

    ```json
    {
      "message": "Error logged"
    }
    ```
    
## 📁Project Structure
   ```  
frienf-math-notes-be/
├── apps/
│   └── calculator/
│       ├── route.py       # API route for /calculate
│       └── utils.py       # Image validation + OpenRouter logic
├── constants.py           # Configuration
├── main.py                # App entry point
├── requirements.txt       # Dependencies
├── schema.py              # Pydantic models
└── README.md              # Documentation
   ```

## Technologies

-   [FastAPI](https://fastapi.tiangolo.com/): High-performance web framework for building APIs.
-   [Python](https://www.python.org/downloads/): Core programming language (3.10+).
-   [Pydantic](https://docs.pydantic.dev/): Data validation and serialization.
-   [PIL (Pillow)](https://pillow.readthedocs.io/en/stable/): Image processing and validation.
-   [OpenRouter API](https://openrouter.ai/): Vision-based analysis of mathematical content.
-   [Uvicorn](https://www.uvicorn.org/): ASGI server for running FastAPI.
-   [python-dotenv](https://pypi.org/project/python-dotenv/): Environment variable management.
-   Logging: Structured logging to console and `app.log`.

## Usage

### Start the Backend:

1.  Run `python main.py` to launch the server at `http://localhost:8900`.
2.  Verify the server is running by accessing `GET /`.

### Integrate with Frontend:

1.  Configure the frontend (frienf-math-notes-fe) to send requests to `http://localhost:8900/calculate`.
2.  Ensure the frontend includes a base64-encoded image and optional `dict_of_vars`.

### Test the API:

1.  Use tools like [Postman](https://www.postman.com/) or [cURL](https://curl.se/) to send a `POST /calculate` request:

    ```bash
    curl -X POST http://localhost:8900/calculate \
      -H "Content-Type: application/json" \
      -d '{"image": "data:image/png;base64,iVBORw0KGgo...", "dict_of_vars": {"x": "4"}}'
    ```
2.  Check the response for evaluated expressions.

### Monitor Logs:

*   View logs in the console or `app.log` for debugging.
*   Errors from the frontend are logged via `POST /log-error`.

## Configuration

### Environment Variables:

*   `OPENROUTER_API_KEY`: Required for [OpenRouter API](https://openrouter.ai/) access.
*   `MAX_IMAGE_PIXELS`: Maximum pixel count for images (default: 10M).
*   `ALLOWED_IMAGE_FORMATS`: Comma-separated list of allowed formats (default: PNG,JPEG).

### Server Settings (in `constants.py`):

*   `SERVER_URL`: Host address (default: `localhost`).
*   `PORT`: Server port (default: `8900`).
*   `ENV`: Environment mode (default: `dev` for auto-reload).

## Security Notes

*   **CORS:** Currently allows all origins (`*`).  Restrict `allow_origins` in `main.py` for production (e.g., `["http://localhost:5173"]` for the frontend).
*   **API Key:** Store `OPENROUTER_API_KEY` securely in `.env` and avoid exposing it in version control.
*   **Image Validation:** Enforces strict checks to prevent processing large or invalid images, mitigating [DoS](https://owasp.org/www-community/attacks/Denial_of_Service) risks.

## Troubleshooting

*   **API Key Error:** Ensure `OPENROUTER_API_KEY` is set in `.env`.  Obtain a key from [OpenRouter](https://openrouter.ai/).
*   **Image Format Error:** Verify the image is a valid PNG or JPEG with a correct base64 data URI prefix.
*   **Large Image Error:** Reduce image size or increase `MAX_IMAGE_PIXELS` in `.env`.
*   **OpenRouter API Failure:** Check logs for model-specific errors (e.g., `x-ai/grok-2-vision-1212`). Ensure API key and internet connectivity.

## Contributing

1.  Fork the [repository](https://github.com/frienf/math-notes-be.git).
2.  Create a feature branch (`git checkout -b feature/your-feature`).
3.  Commit changes (`git commit -m "Add your feature"`).
4.  Push to the branch (`git push origin feature/your-feature`).
5.  Open a pull request.

## License

This project is licensed under the [Apache License 2.0](LICENSE).

## Contact

For questions or feedback, open an issue or contact Deepak Gond.
