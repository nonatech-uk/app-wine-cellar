from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config.settings import settings

router = APIRouter()


@router.get("/labels/{filename}")
def get_label(filename: str):
    # Sanitise filename
    safe = Path(filename).name
    path = Path(settings.label_storage_path) / safe
    if not path.is_file():
        raise HTTPException(404, "Label not found")
    return FileResponse(path)
