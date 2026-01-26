"""Newspapers API."""
from fastapi import APIRouter

from app.config import NEWSPAPERS

router = APIRouter(prefix="/newspapers", tags=["newspapers"])


@router.get("")
def list_newspapers():
    """List available newspapers for scraping."""
    return {"newspapers": NEWSPAPERS}
