# MedCare

MedCare is a single-hospital appointment and care-management platform for three Phase 1 roles: `Patient`, `Doctor`, and `Admin`.

## Project Overview

The platform is designed to solve two connected problems:

- Patients need an easy way to discover doctors, check availability, and book appointments online.
- Hospitals need a secure system to onboard trusted doctors, manage schedules, oversee appointments, and protect sensitive medical data.

## Phase 1 Scope

- Single hospital deployment
- Three active roles: Patient, Doctor, Admin
- One shared login page for all roles
- Role-specific registration flows
- Invitation-based doctor onboarding
- Mock payment flow
- Auto-confirmed appointments after successful mock payment
- Email-only notifications
- No Google sign-in in Phase 1

## Authentication Flow

- One shared login page for `Admin`, `Doctor`, and `Patient`
- Login uses `email + password` only
- System detects role from the database and redirects to the correct dashboard
- One email can belong to only one account and one role

Registration differs by role:
- `Patient` → self-registration with OTP verification
- `Doctor` → invite-only registration with OTP verification
- `Admin` → seeded directly into the database

## Core Roles

### Patient

- Register with name, phone, email, password, and date of birth
- Verify email with OTP
- Browse doctors from the dashboard
- View doctor cards with specialty, experience, rating, and booking action
- Book appointments using: doctor → slot → patient details → mock payment
- See age auto-calculated from date of birth during booking
- View upcoming appointments, history, and prescriptions
- Cancel or reschedule up to 2 hours before the appointment
- Leave one review only after appointment status becomes `Completed`

### Doctor

- Join only through an admin-issued invitation
- Verify invitation and OTP during onboarding
- Complete core registration
- Complete a mandatory one-time professional profile setup
- Edit only working hours and working days after profile submission
- View upcoming appointments
- View only their own patient-related data
- Add prescriptions and consultation notes
- View appointment history

### Admin

- Has no registration page
- Logs in through the same shared login page
- Sends doctor invitations
- Tracks invite states: `Pending`, `Accepted`, `Expired`, `Revoked`
- Resends or revokes invitations
- Views doctor profiles, schedules, and statuses
- Oversees appointments operationally
- Hides abusive reviews
- Does not get clinical-data access in Phase 1

## Key Rules

- Clinical data is visible only to the doctor-patient pair it belongs to
- Admin views are operational only and must not expose prescriptions or medical notes
- Password reset must not reveal whether an email exists
- Sensitive medical data should be protected at rest
- Doctors cannot remove booked availability without cancelling or rescheduling the appointment first
- Booking must protect against slot conflicts with a temporary hold and a unique constraint

## Appointment Flow

1. Patient chooses doctor and date/time
2. System temporarily holds the slot
3. Patient confirms details: name, auto-calculated age, phone
4. Mock payment is completed
5. Appointment becomes `Confirmed`
6. Later it can move to `Completed`, `Cancelled`, `No-Show`, or `Rescheduled`

## Doctor Onboarding Flow

1. Admin sends doctor invitation
2. Doctor opens invite link and confirms email
3. Doctor enters email + password and verifies OTP
4. Doctor completes core registration
5. Doctor fills a one-time profile form:
   - qualification
   - specialty
   - years of experience
   - services
   - working hours
   - working days
   - availability
6. Doctor workspace is created
7. After that, only working hours and working days remain editable

## Core Features

- Unified login with role-based redirection
- Patient OTP registration
- Doctor invite-only onboarding with OTP
- Doctor discovery and appointment booking
- Role-based and relationship-based access control
- Patient, doctor, and admin dashboards
- Structured prescription and medical note handling
- Review system with moderation support

## Current Goal

Build a practical Phase 1 healthcare platform that keeps workflows simple, onboarding controlled, and clinical data properly protected.
