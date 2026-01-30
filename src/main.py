from fastapi import FastAPI, Depends, HTTPException, status, Query
from src.services.queries import (
    get_appointments_by_date_and_doctor,
    get_doctor,
    get_patient,
    create_appointment,
    create_doctor,
    create_patient,
)
from src.schemas.schema import (
    PatientCreate,
    PatientRead,
    DoctorCreate,
    DoctorRead,
    AppointmentCreate,
    AppointmentRead,
)
from src.database import get_db
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List

app = FastAPI(title="Patient Encounter System")


@app.get("/patients/{id}", response_model=PatientRead)
def retrieve_patient(id: int, db: Session = Depends(get_db)):
    patient = get_patient(db, id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )
    return patient


@app.post("/patients", response_model=PatientRead, status_code=201)
def post_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
):
    return create_patient(db, patient)


@app.get("/doctors/{id}", response_model=DoctorRead)
def retrieve_doctor(id: int, db: Session = Depends(get_db)):
    doctor = get_doctor(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found"
        )
    return doctor


@app.post("/doctors", response_model=DoctorRead, status_code=201)
def post_doctor(
    doctor: DoctorCreate,
    db: Session = Depends(get_db),
):
    return create_doctor(db, doctor)


@app.get("/appointments", response_model=List[AppointmentRead])
def list_appointments_endpoint(
    date: date = Query(..., description="YYYY-MM-DD"),
    doctor_id: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db),
):
    return get_appointments_by_date_and_doctor(db, date, doctor_id)


@app.post(
    "/appointments", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED
)
def create_appointment_endpoint(
    payload: AppointmentCreate, db: Session = Depends(get_db)
):
    try:
        return create_appointment(db, payload)
    except HTTPException as exc:
        # propagate 409 for overlapping appointments
        if exc.status_code == status.HTTP_409_CONFLICT:
            raise exc
        # otherwise raise 400 for other validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.detail)
        )


@app.get("/health")
async def health_check():
    return {"status": "UP"}
