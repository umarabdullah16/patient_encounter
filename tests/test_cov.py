import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, time, timezone
import uuid

from src.main import app
from src.database import engine, get_db
from src.models.model import Base
from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import Session
from sqlalchemy.engine.base import Engine
from src.database import SessionLocal

# ----------------------------
# Setup Test DB
# ----------------------------
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Create tables once for tests
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    # Ensure a clean start by dropping any existing tables first (defensive)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ----------------------------
# Client fixture
# ----------------------------
@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ----------------------------
# Fixtures for resources
# ----------------------------
@pytest.fixture(scope="module")
def patient_id(client):
    unique_email = f"john_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "fname": "John",
        "lname": "Doe",
        "email": unique_email,
        "ph_no": "1234567890",
        "age": 30,
    }
    r = client.post("/patients", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture(scope="module")
def doctor_id(client):
    unique_name = f"Dr. Smith {uuid.uuid4().hex[:4]}"
    payload = {"full_name": unique_name, "specialty": "Cardiology", "active": True}
    r = client.post("/doctors", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture(scope="module")
def base_time():
    # Zero microseconds to avoid sub-second boundary issues in overlaps
    return datetime.now(timezone.utc).replace(microsecond=0)


@pytest.fixture(scope="module")
def first_appointment(client, patient_id, doctor_id, base_time):
    start_time = (base_time + timedelta(hours=1)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Checkup",
        "start_time": start_time,
        "duration": 60,
    }
    r = client.post("/appointments", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


# ----------------------------
# Patient tests
# ----------------------------
def test_get_patient(client, patient_id):
    r = client.get(f"/patients/{patient_id}")
    assert r.status_code == 200
    assert r.json()["id"] == patient_id


def test_get_nonexistent_patient(client):
    r = client.get("/patients/9999")
    assert r.status_code == 404


def test_create_patient_invalid_email(client):
    payload = {"fname": "X", "lname": "Y", "email": "bad", "ph_no": "123", "age": 20}
    r = client.post("/patients", json=payload)
    assert r.status_code == 422


# ----------------------------
# Doctor tests
# ----------------------------
def test_get_doctor(client, doctor_id):
    r = client.get(f"/doctors/{doctor_id}")
    assert r.status_code == 200
    assert r.json()["id"] == doctor_id


def test_get_nonexistent_doctor(client):
    r = client.get("/doctors/9999")
    assert r.status_code == 404


"""
def test_create_doctor_invalid(client):
    payload = {"full_name": "", "specialty": "", "active": True}
    r = client.post("/doctors", json=payload)
    assert r.status_code == 400
"""


# ----------------------------
# Appointment tests
# ----------------------------


def test_create_appointment(client, patient_id, doctor_id, base_time):
    start_time = (base_time + timedelta(hours=2)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Follow-up",
        "start_time": start_time,
        "duration": 45,
    }
    r = client.post("/appointments", json=payload)
    assert r.status_code == 201


def test_appointment_conflict(
    client, first_appointment, patient_id, doctor_id, base_time
):
    # Overlapping appointment → 409
    start_time = (base_time + timedelta(hours=1, minutes=30)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Conflict Test",
        "start_time": start_time,
        "duration": 60,
    }
    r = client.post("/appointments", json=payload)
    assert r.status_code == 409


def test_appointment_invalid_duration(client, patient_id, doctor_id, base_time):
    # Duration too short → 400
    start_time = (base_time + timedelta(hours=3)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Short",
        "start_time": start_time,
        "duration": 10,
    }
    r = client.post("/appointments", json=payload)
    assert r.status_code == 422


"""
def test_appointment_outside_working_hours(client, patient_id, doctor_id, base_time):
    # Outside 9:00–18:00 → 400
    # force start_time to 20:00 UTC today
    today = base_time.date()
    start_time = datetime.combine(today, time(hour=20, tzinfo=timezone.utc)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Night Appointment",
        "start_time": start_time,
        "duration": 60,
    }
    r = client.post("/appointments", json=payload)
    assert r.status_code == 400
"""


def test_get_appointments_by_date(client, base_time):
    date_str = base_time.date().isoformat()
    r = client.get(f"/appointments?date={date_str}")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ----------------------------
# Test engine creation
# ----------------------------
def test_engine_created():
    assert isinstance(engine, Engine)
    # Optional: check the URL contains mysql
    assert "mysql" in str(engine.url)


# ----------------------------
# Test SessionLocal factory
# ----------------------------
def test_sessionlocal():
    session = SessionLocal()
    from sqlalchemy.orm.session import Session as SQLASession

    assert isinstance(session, SQLASession)
    session.close()


# ----------------------------
# Test get_db generator
# ----------------------------
def test_get_db():
    gen = get_db()
    db = next(gen)
    # Should return a Session instance
    assert isinstance(db, Session)
    # Closing generator
    try:
        next(gen)
    except StopIteration:
        pass


# ----------------------------
# Test multiple get_db usage
# ----------------------------
def test_get_db_multiple_calls():
    gen1 = get_db()
    db1 = next(gen1)
    gen2 = get_db()
    db2 = next(gen2)
    assert db1 != db2  # Each generator should produce a new session
    # Cleanup
    for gen in [gen1, gen2]:
        try:
            next(gen)
        except StopIteration:
            pass
