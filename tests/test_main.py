import pytest
import requests
from requests.exceptions import ConnectionError, Timeout
from datetime import datetime, timedelta, timezone
import uuid

BASE_URL = "http://127.0.0.1:8000"


# ----------------------------
# Server availability test
# ----------------------------
def test_server_is_reachable():
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code in (200, 404)
    except (ConnectionError, Timeout):
        pytest.fail("Server is NOT reachable")


# ----------------------------
# Fixtures to create resources
# ----------------------------
@pytest.fixture(scope="module")
def patient_id():
    unique_email = f"john_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "fname": "John",
        "lname": "Doe",
        "email": unique_email,
        "ph_no": "1234567890",
        "age": 30,
    }
    r = requests.post(f"{BASE_URL}/patients", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture(scope="module")
def doctor_id():
    payload = {"full_name": "Dr. Smith", "specialty": "Cardiology", "active": True}
    r = requests.post(f"{BASE_URL}/doctors", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.fixture(scope="module")
def base_time():
    # Use a single base time for the module to make time-based tests deterministic
    # Zero microseconds to avoid sub-second boundary flakiness
    return datetime.now(timezone.utc).replace(microsecond=0)


@pytest.fixture(scope="module")
def appointment_id(patient_id, doctor_id, base_time):
    start_time = (base_time + timedelta(hours=1)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Checkup",
        "start_time": start_time,
        "duration": 60,
    }
    r = requests.post(f"{BASE_URL}/appointments", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


# ----------------------------
# Patient tests
# ----------------------------
def test_get_patient(patient_id):
    r = requests.get(f"{BASE_URL}/patients/{patient_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == patient_id


def test_get_nonexistent_patient():
    r = requests.get(f"{BASE_URL}/patients/9999")
    assert r.status_code == 404


# ----------------------------
# Doctor tests
# ----------------------------
def test_get_doctor(doctor_id):
    r = requests.get(f"{BASE_URL}/doctors/{doctor_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == doctor_id


def test_get_nonexistent_doctor():
    r = requests.get(f"{BASE_URL}/doctors/9999")
    assert r.status_code == 404


# ----------------------------
# Appointment tests
# ----------------------------
"""
def test_appointment_conflict(patient_id, doctor_id, base_time):
    start_time = (base_time + timedelta(hours=1, minutes=30)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Follow-up",
        "start_time": start_time,
        "duration": 60,
    }
    r = requests.post(f"{BASE_URL}/appointments", json=payload)
    assert r.status_code == 409
"""


def test_get_appointments_by_date(base_time):
    today = base_time.date().isoformat()
    r = requests.get(f"{BASE_URL}/appointments?date={today}")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
