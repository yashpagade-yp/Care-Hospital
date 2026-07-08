# Project Information Document — MedCare Hospital & Doctor Platform

## 1. Project Overview
A three-role (Admin, Doctor, Patient) web platform for hospital/clinic management, covering doctor onboarding, appointment booking, dashboards, and secure medical data handling.

---

## 2. User Roles

### 2.0 Authentication — Final Flow
- Google sign-in is removed for all roles in Phase 1
- Registration is role-separated, but login is unified
- One shared login page is used by Admin, Doctor, and Patient
- User enters email + password, system checks the database, detects the role, and redirects to the correct workspace
- Email is globally unique across the `User` table: one email = one account = one role

---

### 2.1 Patient
**Registration**
- Fields: name, phone, email, password, date of birth
- OTP is sent to email for verification
- Account and workspace are created after successful verification

**Login**
- Uses the shared login page with email + password

**Features**
- Landing page with hero, specialties, doctor search
- Patient dashboard shows doctor cards with name, specialty, years of experience, rating, and a `Book Appointment` button
- Book appointment flow:
  1. Choose doctor → pick date/time
  2. Patient details → name, age (auto-calculated from DOB), phone
  3. Confirm & pay (mock payment)
- Address is not part of the standard booking flow in Phase 1
- Patient dashboard: upcoming appointments, appointment history, prescriptions/reports (only their own)
- Testimonials/reviews are optional and allowed only after appointment status = `Completed`

---

### 2.2 Admin
**Account**
- Admin is seeded directly into the database
- There is no admin registration page

**Login**
- Uses the same shared login page as Doctor and Patient

**Features**
- **Doctor invitation system**
  - Enter doctor's email → system generates secure token-based invite link (+ optional backup code) → sent via email
  - Invite expires after a set window (e.g., 48–72 hrs)
  - View invite status: `Pending` / `Accepted` / `Expired`
  - Resend invite (new token) or Revoke invite
- **Doctor management**
  - View list of all invited/registered doctors
  - View each doctor's profile: name, specialty, qualification, years of experience, services, contact, status
  - View (not edit by default) each doctor's availability/schedule
  - Override availability in exceptional cases (e.g., emergency leave)
  - Open question: whether admin should have an override path to correct locked doctor profile fields if entered incorrectly
- **Operational oversight**
  - View all appointments across all doctors
  - Access patient-doctor mapping for operational purposes such as scheduling and billing
- **Restricted clinical data access**
  - By default, admin does not see prescriptions or medical notes
  - There is no separate super-admin role in Phase 1

---

### 2.3 Doctor
**Onboarding Flow**
1. Admin invites doctor by entering email
2. Doctor opens the link and confirms the invitation email
3. Doctor enters email + password, OTP is sent to email, and doctor verifies OTP
4. Registration page opens and doctor enters core credentials: name, email, password
5. A mandatory one-time profile form appears with:
   - Degree / qualification
   - Specialty / domain
   - Years of experience
   - Services offered
   - Working hours, working days, and availability
6. Doctor workspace is created after submission
7. After submission, only working hours and working days remain editable; all other profile fields are locked

**Login**
- Uses the same shared login page as Admin and Patient with email + password

**Doctor Dashboard Features**
- View upcoming appointments (patient name, time, reason for visit if provided)
- View patient details relevant to their own appointments only
- Edit own availability — working hours/days only
- Add prescriptions/notes for a patient after consultation
- View appointment history with each patient

---

## 2.4 Login Summary
- One shared login page for Admin, Doctor, and Patient
- Email + password only
- System checks DB, detects role, and redirects to the correct workspace
- Registration is separate per role:
  - Admin → seeded
  - Doctor → invite-only
  - Patient → open self-registration
- Unique email constraint across the entire `User` table

---

## 3. Access Control Matrix (Summary)

| Data / Action | Patient | Doctor | Admin |
|---|---|---|---|
| Own profile/appointments | Full access | Full access (own) | View (operational) |
| Other patients' records | No access | No access | No access |
| Prescriptions/medical notes | Own only | Own patients only | No access |
| Doctor availability | View only | Set/edit own | View + override |
| Doctor invitation management | No access | No access | Full |
| Appointment scheduling overview | Own only | Own only | All (operational) |

---

## 4. Invitation System Details
- **Mechanism:** Secure token embedded in a clickable link (primary), with an optional short backup code shown in the email
- **Expiry:** 48–72 hours (configurable)
- **States:** `Pending`, `Accepted`, `Expired`, `Revoked`
- **Admin actions:** Resend (issues new token), Revoke (invalidates token)
- **Doctor experience on expired link:** Clear message — "This invite has expired, please contact the admin to resend"

---

## 5. Security & Compliance Notes
- Role-based + relationship-based access control (not flat admin-sees-all)
- Encrypt sensitive medical data at rest
- Audit logs for: admin overrides, invite resend/revoke actions
- OTP verification for doctor onboarding identity check
- Standard auth security: no confirmation/denial of whether an email is registered during password reset

---

## 6. Core Modules Summary
1. **Patient Module** — Landing page, auth, doctor discovery, booking, dashboard
2. **Admin Module** — Doctor invitations, doctor directory, and operational appointment overview
3. **Doctor Module** — Invite acceptance + OTP + registration, dashboard, availability management, patient appointment & prescription handling

---

## 7. Phase 1 Finalized Decisions

| Decision | Answer |
|---|---|
| Single or multi-hospital | Single hospital |
| Payment | Mock payment (real gateway swapped in later) |
| Appointment approval | Auto-confirm on successful mock payment (no manual doctor approval) |
| Doctor verification documents | Not required — invite-only model implies trust; OTP confirms email ownership only |
| Cancellation/reschedule policy | Patient: cancel/reschedule up to 2 hrs before appointment; Doctor: cancel anytime |
| Admin tiers | Single admin role only — no super-admin in Phase 1 |
| Notifications | Email only (OTP, invite, confirmation, cancellation) — SMS/WhatsApp/reminders deferred to Phase 2 |
| Prescriptions | Structured text (medicines + notes), no file upload in Phase 1; PDF download is a nice-to-have |
| Reviews | One review per appointment, allowed only after status = Completed; admin can hide (not delete) abusive reviews |

---

## 8. Appointment Lifecycle (State Machine)
`Pending Payment/Held Slot` → `Confirmed` (on successful mock payment) → `Completed` (doctor marks done) / `Cancelled` (by patient or doctor, with cancelledBy + cancelReason) / `No-Show` (doctor marks) / `Rescheduled` (old appointment linked to new appointment id)

---

## 9. Doctor Status Lifecycle
`Invited` → `Registered` (after OTP + profile setup) → `Active` (can receive bookings). `Suspended` available as a manual admin action if needed.

---

## 10. Key System Rules
- **Slot conflict protection:** Unique DB constraint on `(doctorId, dateTime)` with temporary slot hold (5–10 minutes) while patient completes booking/payment
- **Availability edits:** Doctor cannot silently remove a slot that already has a booked appointment — must cancel/reschedule that appointment first
- **Admin appointment view:** Shows only doctorId, patientId, dateTime, status — never joined with prescription/clinical notes
- **Clinical data access:** Strictly doctor + patient only, no admin override in Phase 1
- **Login model:** One shared login page for all roles, no Google login anywhere in Phase 1
- **Profile locking:** For doctors, only working hours and working days remain editable after the one-time profile submission

---

## 11. Next Steps
- Finalize tech stack (frontend, backend, database, auth provider, hosting)
- Define database schema with field types and relationships
- Define API contracts for each module
- Begin UI implementation based on agreed wireframes (landing page, auth, dashboards)
