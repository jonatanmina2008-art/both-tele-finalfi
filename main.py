import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.database import engine
from dotenv import load_dotenv
from routers import auth, accounts, payments

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up SHOPTHALEX backend...")
    yield
    logger.info("Shutting down SHOPTHALEX backend...")
    await engine.dispose()

app = FastAPI(title="SHOPTHALEX API", lifespan=lifespan)

# CORS configuration for Next.js panel interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with Vercel panel domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(payments.router)

@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
