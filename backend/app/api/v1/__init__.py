from fastapi import APIRouter
from .ledger import router as ledger_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ledger_router)
