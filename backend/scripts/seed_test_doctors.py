"""Seed and clean up a reversible batch of development-only doctor accounts.

Run from the Care-Hospital repository root:

    backend/.venv/Scripts/python.exe backend/scripts/seed_test_doctors.py seed
    backend/.venv/Scripts/python.exe backend/scripts/seed_test_doctors.py cleanup

The script identifies its records exclusively through the reserved seed
subdomain ``@seed-doctors.medcare.example.com``. It never updates or deletes a
genuine doctor account.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.commons.auth import encrypt_password  # noqa: E402


SEED_EMAIL_DOMAIN = "seed-doctors.medcare.example.com"
SEED_EMAIL_PATTERN = rf"^[a-z0-9.]+@{SEED_EMAIL_DOMAIN.replace('.', r'\.')}$"
DEFAULT_PASSWORD_ENV = "SEED_DOCTOR_PASSWORD"


DOCTORS: tuple[dict[str, Any], ...] = (
    {
        "name": "Dr. Aarav Sharma",
        "email": f"aarav.sharma@{SEED_EMAIL_DOMAIN}",
        "specialty": "General Medicine",
        "qualification": "MBBS, MD (General Medicine)",
        "experience_years": 6,
        "services": ["General consultation", "Preventive care", "Diabetes management"],
        "schedule": (("MONDAY", "09:00", "13:00"), ("WEDNESDAY", "09:00", "13:00"), ("FRIDAY", "14:00", "18:00")),
    },
    {
        "name": "Dr. Priya Nair",
        "email": f"priya.nair@{SEED_EMAIL_DOMAIN}",
        "specialty": "General Medicine",
        "qualification": "MBBS, DNB (Family Medicine)",
        "experience_years": 11,
        "services": ["General consultation", "Fever and infection care", "Chronic disease management"],
        "schedule": (("TUESDAY", "10:00", "14:00"), ("THURSDAY", "10:00", "14:00"), ("SATURDAY", "09:00", "12:00")),
    },
    {
        "name": "Dr. Rohan Kulkarni",
        "email": f"rohan.kulkarni@{SEED_EMAIL_DOMAIN}",
        "specialty": "General Medicine",
        "qualification": "MBBS, MD (Internal Medicine)",
        "experience_years": 9,
        "services": ["Adult primary care", "Hypertension management", "Health check-ups"],
        "schedule": (("MONDAY", "15:00", "19:00"), ("THURSDAY", "15:00", "19:00"), ("SATURDAY", "10:00", "14:00")),
    },
    {
        "name": "Dr. Meera Iyer",
        "email": f"meera.iyer@{SEED_EMAIL_DOMAIN}",
        "specialty": "General Medicine",
        "qualification": "MBBS, MD (General Medicine)",
        "experience_years": 15,
        "services": ["General consultation", "Geriatric care", "Lifestyle counselling"],
        "schedule": (("TUESDAY", "08:30", "12:30"), ("WEDNESDAY", "14:00", "18:00"), ("FRIDAY", "08:30", "12:30")),
    },
    {
        "name": "Dr. Arjun Patel",
        "email": f"arjun.patel@{SEED_EMAIL_DOMAIN}",
        "specialty": "Orthopedics",
        "qualification": "MBBS, MS (Orthopaedics)",
        "experience_years": 8,
        "services": ["Joint pain treatment", "Fracture care", "Sports injury consultation"],
        "schedule": (("MONDAY", "10:00", "14:00"), ("WEDNESDAY", "16:00", "20:00"), ("SATURDAY", "10:00", "14:00")),
    },
    {
        "name": "Dr. Kavya Reddy",
        "email": f"kavya.reddy@{SEED_EMAIL_DOMAIN}",
        "specialty": "Orthopedics",
        "qualification": "MBBS, DNB (Orthopaedics)",
        "experience_years": 5,
        "services": ["Bone and joint consultation", "Arthritis care", "Back pain treatment"],
        "schedule": (("TUESDAY", "09:00", "13:00"), ("THURSDAY", "14:00", "18:00"), ("FRIDAY", "14:00", "18:00")),
    },
    {
        "name": "Dr. Vikram Singh",
        "email": f"vikram.singh@{SEED_EMAIL_DOMAIN}",
        "specialty": "Orthopedics",
        "qualification": "MBBS, MS, MCh (Orthopaedics)",
        "experience_years": 18,
        "services": ["Joint replacement consultation", "Trauma care", "Spine assessment"],
        "schedule": (("MONDAY", "16:00", "20:00"), ("THURSDAY", "09:00", "13:00"), ("SATURDAY", "15:00", "19:00")),
    },
    {
        "name": "Dr. Sneha Joshi",
        "email": f"sneha.joshi@{SEED_EMAIL_DOMAIN}",
        "specialty": "Orthopedics",
        "qualification": "MBBS, MS (Orthopaedics)",
        "experience_years": 12,
        "services": ["Pediatric orthopedics", "Sports injuries", "Rehabilitation planning"],
        "schedule": (("TUESDAY", "15:00", "19:00"), ("WEDNESDAY", "10:00", "14:00"), ("FRIDAY", "15:00", "19:00")),
    },
    {
        "name": "Dr. Ananya Deshmukh",
        "email": f"ananya.deshmukh@{SEED_EMAIL_DOMAIN}",
        "specialty": "Cardiology",
        "qualification": "MBBS, MD, DM (Cardiology)",
        "experience_years": 14,
        "services": ["Cardiac consultation", "Hypertension care", "Preventive cardiology"],
        "schedule": (("MONDAY", "09:00", "12:00"), ("WEDNESDAY", "15:00", "19:00"), ("FRIDAY", "09:00", "12:00")),
    },
    {
        "name": "Dr. Rahul Verma",
        "email": f"rahul.verma@{SEED_EMAIL_DOMAIN}",
        "specialty": "Pediatrics",
        "qualification": "MBBS, MD (Pediatrics)",
        "experience_years": 10,
        "services": ["Child health consultation", "Growth monitoring", "Vaccination guidance"],
        "schedule": (("TUESDAY", "10:00", "14:00"), ("THURSDAY", "16:00", "20:00"), ("SATURDAY", "09:00", "13:00")),
    },
    {
        "name": "Dr. Ishita Banerjee",
        "email": f"ishita.banerjee@{SEED_EMAIL_DOMAIN}",
        "specialty": "Dermatology",
        "qualification": "MBBS, MD (Dermatology)",
        "experience_years": 7,
        "services": ["Skin consultation", "Acne treatment", "Hair and scalp care"],
        "schedule": (("MONDAY", "14:00", "18:00"), ("WEDNESDAY", "10:00", "14:00"), ("SATURDAY", "14:00", "18:00")),
    },
    {
        "name": "Dr. Neha Kapoor",
        "email": f"neha.kapoor@{SEED_EMAIL_DOMAIN}",
        "specialty": "Gynecology",
        "qualification": "MBBS, MS (Obstetrics and Gynaecology)",
        "experience_years": 13,
        "services": ["Women's health consultation", "Antenatal care", "Menstrual health care"],
        "schedule": (("TUESDAY", "09:00", "13:00"), ("THURSDAY", "09:00", "13:00"), ("FRIDAY", "15:00", "19:00")),
    },
    {
        "name": "Dr. Aditya Rao",
        "email": f"aditya.rao@{SEED_EMAIL_DOMAIN}",
        "specialty": "Neurology",
        "qualification": "MBBS, MD, DM (Neurology)",
        "experience_years": 16,
        "services": ["Neurological consultation", "Headache care", "Movement disorder assessment"],
        "schedule": (("MONDAY", "10:00", "14:00"), ("WEDNESDAY", "15:00", "19:00"), ("SATURDAY", "10:00", "14:00")),
    },
    {
        "name": "Dr. Pooja Menon",
        "email": f"pooja.menon@{SEED_EMAIL_DOMAIN}",
        "specialty": "ENT",
        "qualification": "MBBS, MS (ENT)",
        "experience_years": 9,
        "services": ["Ear and hearing care", "Sinus treatment", "Throat consultation"],
        "schedule": (("TUESDAY", "14:00", "18:00"), ("THURSDAY", "10:00", "14:00"), ("SATURDAY", "09:00", "13:00")),
    },
    {
        "name": "Dr. Siddharth Gupta",
        "email": f"siddharth.gupta@{SEED_EMAIL_DOMAIN}",
        "specialty": "Ophthalmology",
        "qualification": "MBBS, MS (Ophthalmology)",
        "experience_years": 11,
        "services": ["Eye examination", "Cataract consultation", "Vision and glaucoma care"],
        "schedule": (("MONDAY", "09:00", "13:00"), ("THURSDAY", "15:00", "19:00"), ("FRIDAY", "09:00", "13:00")),
    },
)


def get_database():
    load_dotenv(BACKEND_DIR / ".env")
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "fastapi_tutorial")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client, client[database_name], database_name


def get_admin_id(database) -> str:
    admin = database.users.find_one({"role": "ADMIN"}, {"_id": 1})
    if not admin:
        raise RuntimeError("No admin account exists. Seed an admin before test doctors.")
    return str(admin["_id"])


def seed_doctors(database, password: str) -> tuple[int, int]:
    if len(password) < 8:
        raise ValueError("The seed doctor password must contain at least 8 characters.")

    admin_id = get_admin_id(database)
    now = datetime.now(timezone.utc)
    created = 0
    skipped = 0

    for doctor in DOCTORS:
        email = doctor["email"]
        if database.users.find_one({"email": email}, {"_id": 1}):
            skipped += 1
            continue

        password_hash = encrypt_password(password)
        user = {
            "name": doctor["name"],
            "email": email,
            "phone": None,
            "dob": None,
            "password_hash": password_hash,
            "role": "DOCTOR",
            "is_otp_verified": True,
            "otp": None,
            "specialty": doctor["specialty"],
            "qualification": doctor["qualification"],
            "experience_years": doctor["experience_years"],
            "services": doctor["services"],
            "doctor_status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        }
        doctor_id = database.users.insert_one(user).inserted_id

        database.doctor_invitations.insert_one(
            {
                "doctor_email": email,
                "token": f"seed-{secrets.token_urlsafe(32)}",
                "status": "ACCEPTED",
                "invited_by_admin_id": admin_id,
                "expires_at": now + timedelta(days=3),
                "created_at": now,
            }
        )

        database.doctor_availabilities.insert_many(
            [
                {
                    "doctor_id": str(doctor_id),
                    "availability_type": "RECURRING",
                    "day_of_week": day,
                    "start_time": start,
                    "end_time": end,
                    "exception_date": None,
                    "created_at": now,
                    "updated_at": now,
                }
                for day, start, end in doctor["schedule"]
            ]
        )
        created += 1

    return created, skipped


def cleanup_doctors(database, *, delete_related_data: bool) -> dict[str, int]:
    seed_users = list(
        database.users.find(
            {"email": {"$regex": SEED_EMAIL_PATTERN, "$options": "i"}},
            {"_id": 1, "email": 1},
        )
    )
    doctor_ids = [str(item["_id"]) for item in seed_users]
    doctor_object_ids = [ObjectId(item) for item in doctor_ids]
    emails = [item["email"] for item in seed_users]

    appointments = list(
        database.appointments.find(
            {"doctor_id": {"$in": doctor_ids}},
            {"_id": 1},
        )
    )
    appointment_ids = [str(item["_id"]) for item in appointments]

    if appointments and not delete_related_data:
        raise RuntimeError(
            f"Cleanup stopped: {len(appointments)} appointment(s) reference seed doctors. "
            "Review them first, then rerun with --delete-related-data."
        )

    deleted: dict[str, int] = {}
    if delete_related_data and appointment_ids:
        deleted["prescriptions"] = database.prescriptions.delete_many(
            {"appointment_id": {"$in": appointment_ids}}
        ).deleted_count
        deleted["payments"] = database.payments.delete_many(
            {"appointment_id": {"$in": appointment_ids}}
        ).deleted_count
        deleted["appointments"] = database.appointments.delete_many(
            {"_id": {"$in": [ObjectId(item) for item in appointment_ids]}}
        ).deleted_count

    deleted["slot_holds"] = database.slot_holds.delete_many(
        {"doctor_id": {"$in": doctor_ids}}
    ).deleted_count
    deleted["availability"] = database.doctor_availabilities.delete_many(
        {"doctor_id": {"$in": doctor_ids}}
    ).deleted_count
    deleted["invitations"] = database.doctor_invitations.delete_many(
        {"doctor_email": {"$in": emails}}
    ).deleted_count
    deleted["doctors"] = database.users.delete_many(
        {"_id": {"$in": doctor_object_ids}}
    ).deleted_count
    return deleted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Create the reversible test doctor batch.")
    seed_parser.add_argument(
        "--password",
        default=os.getenv(DEFAULT_PASSWORD_ENV),
        help=f"Shared test password. Prefer the {DEFAULT_PASSWORD_ENV} environment variable.",
    )

    cleanup_parser = subparsers.add_parser("cleanup", help="Delete only this test doctor batch.")
    cleanup_parser.add_argument(
        "--delete-related-data",
        action="store_true",
        help="Also delete appointments, prescriptions, and payments tied to seed doctors.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    client, database, database_name = get_database()
    try:
        if args.command == "seed":
            if not args.password:
                raise RuntimeError(
                    f"Provide --password or set {DEFAULT_PASSWORD_ENV} before seeding."
                )
            created, skipped = seed_doctors(database, args.password)
            print(f"Database: {database_name}")
            print(f"Seed doctors created: {created}")
            print(f"Seed doctors already present: {skipped}")
        else:
            deleted = cleanup_doctors(
                database,
                delete_related_data=args.delete_related_data,
            )
            print(f"Database: {database_name}")
            for record_type, count in deleted.items():
                print(f"Deleted {record_type}: {count}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
