from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Boolean, Text, func
from sqlalchemy.orm import relationship
from .database import Base


class Technician(Base):
    __tablename__ = "technicians"

    technician_id = Column(String(20), primary_key=True)
    technician_name = Column(String(100), nullable=False)
    test_department = Column(String(50))


class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Package(Base):
    __tablename__ = "packages"

    package_id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String(150), nullable=False)
    test_department = Column(String(50), nullable=False)
    default_location = Column(String(50), nullable=False)
    default_qty = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    lots = relationship("Lot", back_populates="package")


class Lot(Base):
    __tablename__ = "lots"

    lot_id = Column(Integer, primary_key=True, index=True)
    lot_number = Column(String(20), unique=True, nullable=False)
    package_id = Column(Integer, ForeignKey("packages.package_id"), nullable=False)
    test_department = Column(String(50), nullable=False)
    rack_location = Column(String(50), nullable=False)
    initial_qty = Column(Integer, nullable=False)
    current_qty = Column(Integer, nullable=False)
    replenish_limit = Column(Integer, nullable=False, default=50)
    total_broken = Column(Integer, nullable=False, default=0)
    total_missing = Column(Integer, nullable=False, default=0)
    total_bent_lead = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    package = relationship("Package", back_populates="lots")
    request_records = relationship("RequestRecord", back_populates="lot")
    history = relationship("LotHistory", back_populates="lot")


class RequestRecord(Base):
    __tablename__ = "borrow_records"

    borrow_id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(20), unique=True, nullable=False)
    lot_id = Column(Integer, ForeignKey("lots.lot_id"), nullable=False)
    technician_id = Column(String(20), ForeignKey("technicians.technician_id"), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    purpose = Column(String(255), nullable=False)
    handler_no = Column(String(50), nullable=False)
    borrow_datetime = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(20), nullable=False, default="pending")

    lot = relationship("Lot", back_populates="request_records")
    technician = relationship("Technician")
    return_record = relationship("ReturnRecord", back_populates="request", uselist=False)


class ReturnRecord(Base):
    __tablename__ = "return_records"

    return_id = Column(Integer, primary_key=True, index=True)
    borrow_id = Column(Integer, ForeignKey("borrow_records.borrow_id"), nullable=False)
    return_qty = Column(Integer, nullable=False)
    good_qty = Column(Integer, nullable=False, default=0)
    broken_qty = Column(Integer, nullable=False, default=0)
    missing_qty = Column(Integer, nullable=False, default=0)
    bent_lead_qty = Column(Integer, nullable=False, default=0)
    returning_technician_id = Column(String(20), ForeignKey("technicians.technician_id"))
    return_datetime = Column(TIMESTAMP, server_default=func.now())
    resolved = Column(Boolean, default=False)
    resolved_at = Column(TIMESTAMP)
    resolved_good_qty = Column(Integer, default=0)
    resolved_broken_qty = Column(Integer, default=0)
    resolved_by = Column(String(50))

    request = relationship("RequestRecord", back_populates="return_record")


class LotHistory(Base):
    __tablename__ = "lot_history"

    history_id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("lots.lot_id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    qty_change = Column(Integer, default=0)
    qty_before = Column(Integer)
    qty_after = Column(Integer)
    location_before = Column(String(50))
    location_after = Column(String(50))
    reason = Column(String(255))
    technician_id = Column(String(20), ForeignKey("technicians.technician_id"))
    admin_username = Column(String(50))
    borrow_id = Column(Integer, ForeignKey("borrow_records.borrow_id"))
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    lot = relationship("Lot", back_populates="history")
