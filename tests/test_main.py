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
        assert response.status_code in (200, 404)  # empty list might return 200 or 404
        print("✔ Server is ON and reachable")
    except (ConnectionError, Timeout):
        pytest.fail("✘ Server is NOT reachable")


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
    print("✔ Patient added successfully")
    return r.json()["id"]


@pytest.fixture(scope="module")
def doctor_id():
    payload = {"full_name": "Dr. Smith", "specialty": "Cardiology", "active": True}
    r = requests.post(f"{BASE_URL}/doctors", json=payload)
    assert r.status_code == 201
    print("✔ Doctor added successfully")
    return r.json()["id"]


# ----------------------------
# Patient tests
# ----------------------------
def test_get_patient(patient_id):
    r = requests.get(f"{BASE_URL}/patients/{patient_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == patient_id
    print("✔ Patient retrieved successfully")


def test_get_nonexistent_patient():
    r = requests.get(f"{BASE_URL}/patients/9999")
    assert r.status_code == 404
    print("✔ Non-existent patient returns 404")


# ----------------------------
# Doctor tests
# ----------------------------
def test_get_doctor(doctor_id):
    r = requests.get(f"{BASE_URL}/doctors/{doctor_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == doctor_id
    print("✔ Doctor retrieved successfully")


def test_get_nonexistent_doctor():
    r = requests.get(f"{BASE_URL}/doctors/9999")
    assert r.status_code == 404
    print("✔ Non-existent doctor returns 404")


# ----------------------------
# Appointment tests
# ----------------------------
@pytest.fixture(scope="module")
def appointment_id(patient_id, doctor_id):
    start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Checkup",
        "start_time": start_time,
        "duration": 60,
    }
    r = requests.post(f"{BASE_URL}/appointments", json=payload)
    assert r.status_code == 201
    print("✔ Appointment created successfully")
    return r.json()["id"]


"""
def test_appointment_conflict(patient_id, doctor_id):
    # Attempt overlapping appointment → should return 409
    start_time = (
        datetime.now(timezone.utc) + timedelta(hours=1, minutes=30)
    ).isoformat()
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "reason": "Follow-up",
        "start_time": start_time,
        "duration": 60,
    }
    r = requests.post(f"{BASE_URL}/appointments", json=payload)
    assert r.status_code == 409
    print("✔ Overlapping appointment returns 409")
"""


def test_get_appointments_by_date():
    today = datetime.now(timezone.utc).date().isoformat()
    r = requests.get(f"{BASE_URL}/appointments?date={today}")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    print("✔ Appointments list fetched successfully")
