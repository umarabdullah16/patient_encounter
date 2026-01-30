from sqlalchemy.orm import Session
from src.models.model import Appointment

from datetime import datetime, date, timedelta, timezone


def has_overlapping_appointment(
    db: Session,
    doctor_id: int,
    start_time: datetime,
    duration: int,
) -> bool:
    """
    Checks if a doctor has an overlapping appointment.

    Args:
        db: SQLAlchemy session
        doctor_id: int
        start_time: datetime (aware)
        duration: int (minutes)

    Returns:
        True if there is a conflicting appointment, False otherwise.
    """
    # Ensure start_time is timezone-aware in UTC
    if start_time.tzinfo is None:
        raise ValueError("start_time must include timezone info")
    start_time_utc = start_time.astimezone(timezone.utc)
    end_time_utc = start_time_utc + timedelta(minutes=duration)

    # Fetch all future appointments for this doctor
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time >= datetime.now(timezone.utc),
        )
        .all()
    )

    # Check for overlap
    for appt in appointments:
        existing_start = appt.start_time.astimezone(timezone.utc)
        existing_end = existing_start + timedelta(minutes=appt.duration)

        # Overlap condition
        if existing_start < end_time_utc and existing_end > start_time_utc:
            return True

    return False


def day_bounds_utc(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    end = start + timedelta(days=1)
    return start, end
