from sqlalchemy import (
    DateTime,
    Boolean,
    String,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func
from datetime import datetime
from src.database import engine


class Base(DeclarativeBase):
    pass


class Patient(Base):
    """
    Represents a patient in the hospital.
    """

    __tablename__ = "umar_patients_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    fname: Mapped[str] = mapped_column(String(100), nullable=False)
    lname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    ph_no: Mapped[int] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # One-to-many relationship: one patient -> many appointments
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class Doctor(Base):
    """
    Represents a doctor in the hospital.
    """

    __tablename__ = "umar_doctors_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")


class Appointment(Base):
    """
    Represents an appointment between a patient and a doctor.
    """

    __tablename__ = "umar_appointments_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("umar_patients_table.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("umar_doctors_table.id"))
    reason: Mapped[str] = mapped_column(String(200))
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    patient: Mapped[Patient] = relationship(back_populates="appointments")
    doctor: Mapped[Doctor] = relationship(back_populates="appointments")


if __name__ == "__main__":
    try:
        Base.metadata.create_all(engine)
        print("Executed")
    except Exception as e:
        print(e)
