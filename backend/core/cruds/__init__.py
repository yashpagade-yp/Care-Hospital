"""CRUD exports for the MedCare backend."""

from backend.core.cruds.appointment_crud import CRUDAppointment
from backend.core.cruds.availability_crud import CRUDDoctorAvailability
from backend.core.cruds.invitation_crud import CRUDDoctorInvitation
from backend.core.cruds.payment_crud import CRUDPayment
from backend.core.cruds.prescription_crud import CRUDPrescription
from backend.core.cruds.review_crud import CRUDReview
from backend.core.cruds.slot_hold_crud import CRUDSlotHold
from backend.core.cruds.user_crud import CRUDUser

__all__ = [
    "CRUDAppointment",
    "CRUDDoctorAvailability",
    "CRUDDoctorInvitation",
    "CRUDPayment",
    "CRUDPrescription",
    "CRUDReview",
    "CRUDSlotHold",
    "CRUDUser",
]
