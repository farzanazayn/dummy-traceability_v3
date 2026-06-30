from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import traceback
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/lots", tags=["lots"])


def _lot_to_out(lot: models.Lot) -> schemas.LotOut:
    return schemas.LotOut(
        lot_id=lot.lot_id,
        lot_number=lot.lot_number,
        package_id=lot.package_id,
        package_name=lot.package.package_name,
        test_department=lot.test_department,
        rack_location=lot.rack_location,
        initial_qty=lot.initial_qty,
        current_qty=lot.current_qty,
        replenish_limit=lot.replenish_limit,
        total_broken=lot.total_broken,
        total_missing=lot.total_missing,
        total_bent_lead=lot.total_bent_lead,
    )


@router.get("", response_model=list[schemas.LotOut])
def list_lots(db: Session = Depends(get_db)):
    lots = db.query(models.Lot).order_by(models.Lot.lot_id).all()
    return [_lot_to_out(lot) for lot in lots]


@router.post("", response_model=schemas.LotOut)
def register_lot(payload: schemas.LotCreate, db: Session = Depends(get_db)):
    try:
        package = db.get(models.Package, payload.package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")

        lot_number = payload.lot_number.strip().upper()
        if not lot_number:
            raise HTTPException(status_code=400, detail="Lot number is required.")

        existing = db.query(models.Lot).filter(models.Lot.lot_number == lot_number).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Lot number '{lot_number}' already exists.")

        lot = models.Lot(
            lot_number=lot_number,
            package_id=package.package_id,
            test_department=package.test_department,
            rack_location=payload.rack_location,
            initial_qty=payload.initial_qty,
            current_qty=payload.initial_qty,
            replenish_limit=payload.replenish_limit,
        )
        db.add(lot)
        db.commit()
        db.refresh(lot)

        history = models.LotHistory(
            lot_id=lot.lot_id,
            action_type="REGISTERED",
            qty_before=0,
            qty_after=payload.initial_qty,
            qty_change=payload.initial_qty,
            reason="Initial lot registration",
            notes=f"Lot {lot_number} registered with {payload.initial_qty} units",
        )
        db.add(history)
        db.commit()
        return _lot_to_out(lot)

    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Lot number already exists.")
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{lot_id}", response_model=schemas.LotOut)
def update_lot(lot_id: int, payload: schemas.LotUpdate, db: Session = Depends(get_db)):
    try:
        lot = db.get(models.Lot, lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")

        admin = db.query(models.Admin).filter(models.Admin.username == payload.admin_username).first()
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid admin session.")

        qty_before = lot.current_qty
        loc_before = lot.rack_location
        lot_number_before = lot.lot_number

        # Handle lot number change
        if payload.lot_number is not None and payload.lot_number.strip():
            new_lot_number = payload.lot_number.strip().upper()
            if new_lot_number != lot.lot_number:
                existing = db.query(models.Lot).filter(
                    models.Lot.lot_number == new_lot_number,
                    models.Lot.lot_id != lot.lot_id
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail=f"Lot number '{new_lot_number}' already exists.")
                lot.lot_number = new_lot_number

        if payload.new_qty is not None:
            lot.current_qty = payload.new_qty
            lot.initial_qty = payload.new_qty

        if payload.rack_location is not None:
            lot.rack_location = payload.rack_location

        # Reset defect counters ONLY on Replenishment
        defect_reset_note = ""
        if payload.reason == "Replenishment":
            lot.total_broken = 0
            lot.total_missing = 0
            lot.total_bent_lead = 0
            defect_reset_note = " | Defect counters reset (Replenishment)"

        action = "QTY_UPDATE" if payload.new_qty is not None else "LOCATION_CHANGE"
        if payload.reason == "Replenishment":
            action = "REPLENISHMENT"
        if lot_number_before != lot.lot_number:
            action = "LOT_NUMBER_CHANGE" if action == "LOCATION_CHANGE" else action

        notes_parts = [f"Updated by {admin.full_name}"]
        if lot_number_before != lot.lot_number:
            notes_parts.append(f"Lot No: {lot_number_before} → {lot.lot_number}")
        notes_parts_str = " | ".join(notes_parts) + defect_reset_note

        history = models.LotHistory(
            lot_id=lot.lot_id,
            action_type=action,
            qty_before=qty_before,
            qty_after=lot.current_qty,
            qty_change=(lot.current_qty - qty_before),
            location_before=loc_before,
            location_after=lot.rack_location,
            reason=payload.reason,
            admin_username=payload.admin_username,
            notes=notes_parts_str,
        )
        db.add(history)
        db.commit()
        db.refresh(lot)
        return _lot_to_out(lot)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{lot_id}")
def delete_lot(lot_id: int, admin_username: str, db: Session = Depends(get_db)):
    try:
        lot = db.get(models.Lot, lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")

        admin = db.query(models.Admin).filter(models.Admin.username == admin_username).first()
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid admin session.")

        active = db.query(models.RequestRecord).filter(
            models.RequestRecord.lot_id == lot_id,
            models.RequestRecord.status.in_(["pending", "borrowed"])
        ).first()

        if active:
            raise HTTPException(status_code=400, detail="Cannot delete lot with active or pending requests.")

        db.delete(lot)
        db.commit()
        return {"message": f"Lot {lot.lot_number} deleted."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lot_id}/history", response_model=list[schemas.LotHistoryOut])
def get_lot_history(lot_id: int, db: Session = Depends(get_db)):
    try:
        lot = db.get(models.Lot, lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")

        history = db.query(models.LotHistory).filter(
            models.LotHistory.lot_id == lot_id
        ).order_by(models.LotHistory.created_at.desc()).all()

        result = []
        for h in history:
            tech_name = None
            if h.technician_id:
                tech = db.get(models.Technician, h.technician_id)
                tech_name = tech.technician_name if tech else h.technician_id

            result.append(schemas.LotHistoryOut(
                history_id=h.history_id,
                lot_id=h.lot_id,
                lot_number=lot.lot_number,
                package_name=lot.package.package_name,
                action_type=h.action_type,
                qty_change=h.qty_change or 0,
                qty_before=h.qty_before,
                qty_after=h.qty_after,
                location_before=h.location_before,
                location_after=h.location_after,
                reason=h.reason,
                technician_name=tech_name,
                admin_username=h.admin_username,
                notes=h.notes,
                created_at=h.created_at,
            ))
        return result

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))