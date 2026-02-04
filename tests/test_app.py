import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from src.main import app
from src.models.model import Base
from src.database import engine, SessionLocal
from src.services import queries as service
from src.schemas.schema import PatientCreate, DoctorCreate, AppointmentCreate

# Ensure a clean DB for these API tests
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ---------------- API TESTS ----------------
def test_create_and_get_patient():
    resp = client.post(
        "/patients",
        json={
            "fname": "John",
            "lname": "Doe",
            "email": "john@example.com",
            "ph_no": "1234567890",
            "age": 30,
        },
    )
    assert resp.status_code == 201
    patient_id = resp.json()["id"]

    get_resp = client.get(f"/patients/{patient_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "john@example.com"


def test_duplicate_patient_email():
    # Reuse same email -> should return 400 due to unique constraint handling
    resp = client.post(
        "/patients",
        json={
            "fname": "Jane",
            "lname": "Smith",
            "email": "john@example.com",  # duplicate
            "ph_no": "5555555555",
            "age": 25,
        },
    )
    assert resp.status_code == 400


def test_get_nonexistent_patient():
    resp = client.get("/patients/9999")
    assert resp.status_code == 404


def test_create_and_get_doctor():
    resp = client.post(
        "/doctors",
        json={
            "full_name": "Dr. Strange",
            "specialty": "Magic",
            "active": True,
        },
    )
    assert resp.status_code == 201
    doctor_id = resp.json()["id"]

    get_resp = client.get(f"/doctors/{doctor_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["specialty"] == "Magic"


def test_get_nonexistent_doctor():
    resp = client.get("/doctors/9999")
    assert resp.status_code == 404


def test_create_valid_appointment():
    patient = client.post(
        "/patients",
        json={
            "fname": "Alice",
            "lname": "Wonder",
            "email": "alice@example.com",
            "ph_no": "5551234567",
            "age": 28,
        },
    ).json()
    doctor = client.post(
        "/doctors",
        json={
            "full_name": "Dr. Brown",
            "specialty": "Dermatology",
            "active": True,
        },
    ).json()

    start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    resp = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "start_time": start_time,
            "duration": 30,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["duration"] == 30


def test_reject_past_appointment():
    patient = client.post(
        "/patients",
        json={
            "fname": "Bob",
            "lname": "Marley",
            "email": "bob@example.com",
            "ph_no": "5559876543",
            "age": 35,
        },
    ).json()
    doctor = client.post(
        "/doctors",
        json={
            "full_name": "Dr. Green",
            "specialty": "Neurology",
            "active": True,
        },
    ).json()

    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    resp = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "start_time": past_time,
            "duration": 30,
        },
    )
    # Pydantic model validation rejects past appointment → 422
    assert resp.status_code == 422


def test_reject_overlapping_appointment():
    patient = client.post(
        "/patients",
        json={
            "fname": "Charlie",
            "lname": "Day",
            "email": "charlie@example.com",
            "ph_no": "5551112222",
            "age": 40,
        },
    ).json()
    doctor = client.post(
        "/doctors",
        json={
            "full_name": "Dr. White",
            "specialty": "Orthopedics",
            "active": True,
        },
    ).json()

    start_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "start_time": start_time,
            "duration": 60,
        },
    )

    resp = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "start_time": start_time,
            "duration": 30,
        },
    )
    assert resp.status_code == 409


def test_list_appointments_by_date():
    today = datetime.now(timezone.utc).date().isoformat()
    resp = client.get(f"/appointments?date={today}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_invalid_date_format():
    resp = client.get("/appointments?date=31-01-2026")
    # Invalid query param → 422
    assert resp.status_code == 422


# ---------------- SERVICE LAYER TESTS ----------------
@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_patient_service_create_and_get(db):
    patient_in = PatientCreate(
        fname="Service",
        lname="User",
        email="service@example.com",
        ph_no="1234567890",
        age=50,
    )
    patient = service.create_patient(db, patient_in)
    assert patient.id is not None
    fetched = service.get_patient(db, patient.id)
    assert fetched.email == "service@example.com"


def test_doctor_service_create_and_get(db):
    doctor_in = DoctorCreate(
        full_name="Dr. Service", specialty="Cardiology", active=True
    )
    doctor = service.create_doctor(db, doctor_in)
    assert doctor.id is not None
    fetched = service.get_doctor(db, doctor.id)
    assert fetched.full_name == "Dr. Service"


def test_appointment_service_create(db):
    patient_in = PatientCreate(
        fname="App",
        lname="Tester",
        email="apptester@example.com",
        ph_no="5555555555",
        age=45,
    )
    patient = service.create_patient(db, patient_in)

    doctor_in = DoctorCreate(
        full_name="Dr. Service", specialty="Dermatology", active=True
    )
    doctor = service.create_doctor(db, doctor_in)

    start_time = datetime.now(timezone.utc) + timedelta(hours=1)
    appt_in = AppointmentCreate(
        patient_id=patient.id,
        doctor_id=doctor.id,
        start_time=start_time,
        duration=30,
    )
    appt = service.create_appointment(db, appt_in)
    assert appt.id is not None
    assert appt.doctor_id == doctor.id
    assert appt.patient_id == patient.id
