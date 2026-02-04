from pydantic import (
    BaseModel,
    EmailStr,
    PositiveInt,
    field_validator,
    model_validator,
    Field,
    constr,
)
from datetime import datetime, timezone
from typing import Optional


class AppointmentCreate(BaseModel):
    patient_id: PositiveInt
    doctor_id: PositiveInt
    reason: Optional[str] = None
    start_time: datetime
    duration: int = Field(ge=15, le=180)

    @field_validator("start_time")
    @classmethod
    def start_time_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("start_time must include timezone information")
        return value

    @model_validator(mode="after")
    def appointment_must_be_in_future(self):
        if self.start_time <= datetime.now(timezone.utc):
            raise ValueError("appointment must be scheduled in the future")
        return self


class AppointmentRead(BaseModel):
    id: PositiveInt
    patient_id: PositiveInt
    doctor_id: PositiveInt
    reason: Optional[str]
    start_time: datetime
    duration: int = Field(ge=15, le=180)

    class Config:
        from_attributes = True


class PatientCreate(BaseModel):
    fname: str
    lname: str
    email: EmailStr
    ph_no: Optional[str] = None
    age: int


class PatientRead(BaseModel):
    id: PositiveInt
    fname: str
    lname: str
    email: EmailStr
    ph_no: Optional[str]
    age: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


"""
class PatientReadWithAppointments(PatientRead):
    appointments: List[AppointmentRead] = []
"""


class DoctorCreate(BaseModel):
    full_name: constr(min_length=2)
    specialty: constr(min_length=2)
    active: bool = True


class DoctorRead(BaseModel):
    id: PositiveInt
    full_name: constr(min_length=2)
    specialty: constr(min_length=2)
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


"""
class DoctorReadWithAppointments(DoctorRead):
    appointments: List[AppointmentRead] = []
"""
