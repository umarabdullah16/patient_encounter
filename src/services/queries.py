from sqlalchemy.orm import Session
from src.models.model import Patient, Doctor, Appointment
from sqlalchemy import select, and_
from datetime import date
from typing import Optional, List
from src.services.utils import has_overlapping_appointment, day_bounds_utc
from fastapi import HTTPException, status


def create_patient(db: Session, patient_data) -> Patient:
    patient = Patient(**patient_data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_patient(db: Session, patient_id: int) -> Patient | None:
    return db.get(Patient, patient_id)


def create_doctor(db: Session, doctor_data) -> Doctor:
    doctor = Doctor(**doctor_data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def get_doctor(db: Session, doctor_id: int) -> Doctor | None:
    return db.get(Doctor, doctor_id)


def create_appointment(db: Session, appointment_data) -> Appointment:
    # overlap protection
    if has_overlapping_appointment(
        db,
        appointment_data.doctor_id,
        appointment_data.start_time,
        appointment_data.duration,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor already has an overlapping appointment",
        )

    appointment = Appointment(**appointment_data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_appointments_by_date(
    db: Session,
    target_date: date,
) -> List[Appointment]:
    start, end = day_bounds_utc(target_date)

    stmt = select(Appointment).where(
        Appointment.start_time >= start,
        Appointment.start_time < end,
    )

    return db.execute(stmt).scalars().all()


def get_appointments_by_date_and_doctor(
    db: Session,
    target_date: date,
    doctor_id: Optional[int] = None,
) -> List[Appointment]:
    start, end = day_bounds_utc(target_date)

    conditions = [
        Appointment.start_time >= start,
        Appointment.start_time < end,
    ]

    if doctor_id is not None:
        conditions.append(Appointment.doctor_id == doctor_id)

    stmt = select(Appointment).where(and_(*conditions))

    return db.execute(stmt).scalars().all()
