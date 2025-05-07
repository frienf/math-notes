from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from apps.calculator.route import router as calculator_router
from constants import SERVER_URL, PORT, ENV
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    yield
    logger.info("Shutting down application")

app = FastAPI(
    lifespan=lifespan,
    title="Predystopic Calculator API",
    description="API for analyzing mathematical expressions and graphical problems from images",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def root():
    return {"message": "Server is running"}

@app.post('/log-error')
async def log_error(request: Request):
    try:
        error_data = await request.json()
        logger.error("Frontend error: %s", error_data)
        return JSONResponse(
            status_code=200,
            content={"message": "Error logged"}
        )
    except Exception as e:
        logger.error("Failed to log frontend error: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={"message": f"Failed to log error: {str(e)}"}
        )

app.include_router(calculator_router, prefix="/calculate", tags=["calculate"])

if __name__ == "__main__":
    logger.info(f"Starting server on {SERVER_URL}:{PORT} in {ENV} mode")
    uvicorn.run("main:app", host=SERVER_URL, port=int(PORT), reload=(ENV == "dev"))