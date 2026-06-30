# Problem Statement

## Project Title
MedCare — Hospital & Doctor Appointment Management Platform

## Background
Patients today struggle to find the right doctor, check availability, and book appointments without long phone calls or in-person visits. Hospitals and clinics, on the other hand, lack a centralized digital system to manage doctor onboarding, schedules, and patient records efficiently. There is a need for a single, secure, role-based web platform that connects **Admin**, **Doctors**, and **Patients** in one seamless system.

## Problem
- Patients have no easy way to discover doctors by specialty, check real-time availability, and book appointments online with a trustworthy, modern interface.
- Hospitals have no controlled way to onboard verified doctors onto a digital platform — open signups risk fake or unverified doctor profiles.
- Doctors lack a dedicated dashboard to manage their appointments and view patient details in one place.
- Admins have no centralized way to manage doctors, oversee schedules, and access operational data without it being scattered across spreadsheets, calls, and manual records.
- Sensitive medical data (prescriptions, patient history) needs controlled, secure access — not open to every internal user by default.

## Objective
To design and build a **production-level, three-role web platform** (Admin, Doctor, Patient) that:
1. Allows patients to register, log in (including Google sign-in), browse doctors, and book appointments seamlessly.
2. Allows admins to invite doctors securely via email invitation (link/token-based), manage doctor records, and oversee appointments at an operational level.
3. Allows doctors to accept invitations via OTP-verified registration, manage their own availability, and access a dashboard showing their appointments and patient details.
4. Enforces strict, role-based and relationship-based access control so that clinical data (prescriptions, medical records) is only accessible to the doctor-patient pair it belongs to, with a separate super-admin tier for any exceptional access — fully logged.
5. Provides a secure, scalable, and user-friendly experience across all three roles, suitable for real-world hospital/clinic use.

## Scope
- Patient-facing landing page, authentication (signup/login/forgot password/Google), doctor discovery, and appointment booking flow.
- Admin dashboard for doctor invitation management, doctor directory, and operational oversight of appointments.
- Doctor dashboard for availability management, appointment view, and patient interaction (prescriptions, notes).
- Secure invitation system (token-based links with expiry, resend, and revoke capability).
- Role-based access control across all data, with audit logging for sensitive actions.

## Expected Outcome
A fully functional, secure, and scalable hospital management web application that streamlines doctor onboarding, simplifies patient appointment booking, and gives admins full operational visibility — without compromising the privacy of sensitive medical data.
