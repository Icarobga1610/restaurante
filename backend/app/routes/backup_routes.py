import os
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.schemas import BackupInfo, ImportResult
from app.auth.auth import get_current_user
from app.services.backup_service import BackupService

router = APIRouter(prefix="/api", tags=["Backup"])


# ── Backup ──────────────────────────────────────────────────────

@router.post("/backups/create", response_model=dict)
def create_backup(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BackupService(db)
    try:
        return service.create_backup(user_id=current_user.id, username=current_user.username)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups/list", response_model=list)
def list_backups(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    service = BackupService(db)
    return service.list_backups()


@router.get("/backups/download/{filename}")
def download_backup(
    filename: str,
    _: User = Depends(get_current_user),
):
    from app.services.backup_service import BACKUP_DIR
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup não encontrado")

    def iterfile():
        with open(filepath, "rb") as f:
            yield from f

    return StreamingResponse(iterfile(), media_type="application/octet-stream",
                              headers={"Content-Disposition": f"attachment; filename={filename}"})


# ── Export ──────────────────────────────────────────────────────

@router.get("/exports/clients")
def export_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BackupService(db)
    filename = service.export_clients()
    service.log_export("clients", filename, current_user.id, current_user.username)
    filepath = os.path.join(service.EXPORT_DIR, filename)
    return _csv_response(filepath, filename)


@router.get("/exports/products")
def export_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BackupService(db)
    filename = service.export_products()
    service.log_export("products", filename, current_user.id, current_user.username)
    filepath = os.path.join(service.EXPORT_DIR, filename)
    return _csv_response(filepath, filename)


@router.get("/exports/stock")
def export_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BackupService(db)
    filename = service.export_stock()
    service.log_export("stock", filename, current_user.id, current_user.username)
    filepath = os.path.join(service.EXPORT_DIR, filename)
    return _csv_response(filepath, filename)


@router.get("/exports/sales")
def export_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BackupService(db)
    filename = service.export_sales()
    service.log_export("sales", filename, current_user.id, current_user.username)
    filepath = os.path.join(service.EXPORT_DIR, filename)
    return _csv_response(filepath, filename)


@router.get("/exports/monthly-accounts")
def export_monthly_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BackupService(db)
    filename = service.export_monthly_accounts()
    service.log_export("monthly_accounts", filename, current_user.id, current_user.username)
    filepath = os.path.join(service.EXPORT_DIR, filename)
    return _csv_response(filepath, filename)


# ── Import ──────────────────────────────────────────────────────

@router.post("/imports/clients", response_model=ImportResult)
async def import_clients(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Apenas arquivos CSV são aceitos")
    content = (await file.read()).decode("utf-8-sig")
    service = BackupService(db)
    result = service.import_clients(content, current_user.id, current_user.username)
    return result


@router.post("/imports/products", response_model=ImportResult)
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Apenas arquivos CSV são aceitos")
    content = (await file.read()).decode("utf-8-sig")
    service = BackupService(db)
    result = service.import_products(content, current_user.id, current_user.username)
    return result


# ── Helpers ─────────────────────────────────────────────────────

def _csv_response(filepath: str, filename: str):
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    def iterfile():
        with open(filepath, "rb") as f:
            yield from f
    return StreamingResponse(
        iterfile(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
