from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import traceback
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/packages", tags=["packages"])


@router.get("", response_model=list[schemas.PackageOut])
def list_packages(db: Session = Depends(get_db)):
    return db.query(models.Package).order_by(
        models.Package.test_department, models.Package.package_name
    ).all()


@router.post("", response_model=schemas.PackageOut)
def create_package(payload: schemas.PackageCreate, db: Session = Depends(get_db)):
    try:
        pkg = models.Package(**payload.model_dump())
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
        return pkg
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{package_id}")
def delete_package(package_id: int, admin_username: str, db: Session = Depends(get_db)):
    try:
        pkg = db.get(models.Package, package_id)
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")
        admin = db.query(models.Admin).filter(models.Admin.username == admin_username).first()
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid admin session.")
        lots = db.query(models.Lot).filter(models.Lot.package_id == package_id).first()
        if lots:
            raise HTTPException(status_code=400, detail="Cannot delete package with registered lots.")
        db.delete(pkg)
        db.commit()
        return {"message": f"Package '{pkg.package_name}' deleted."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
