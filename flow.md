#  Full Project Flow Documentation

## 1. Full Project Flow (High-Level Overview)

1. **Admin** is seeded directly into the database (no registration page exists for admin).
2. **Admin logs in** via the shared login page and invites a **Doctor** by entering their email.
3. **Doctor** receives an invitation email, verifies the token, sets email/password, verifies OTP, and completes a **one-time mandatory profile form** (specialty, qualification, experience, services, working hours/days). This creates the doctor's workspace.
4. **Patient** visits the website, self-registers (name, phone, email, password, DOB), verifies OTP, and lands on their dashboard.
5. **Patient** browses doctor profiles (specialty, experience, rating) and books an appointment in a 3-step flow: choose doctor + slot → patient details → confirm & pay (mock).
6. **Doctor** logs in via the same shared login page, sees the new appointment on their dashboard, and can later add a prescription after the consultation.
7. **Admin** can view all appointments and doctor records operationally (not clinical data) at any point.
8. All three roles — Admin, Doctor, Patient — use **one shared login page** (email + password, no Google), with the system routing each to their correct workspace based on role.

---

## 2. Admin Flow (Step by Step)

1. Admin account already exists in DB (seeded manually — no signup).
2. Admin opens the shared login page → enters email + password.
3. System verifies credentials → detects role = `admin` → redirects to **Admin Dashboard**.
4. **Invite a Doctor:**
   - Admin enters the doctor's email in the "Invite Doctor" form.
   - System generates a secure token, creates a `DoctorInvitation` record (status: `pending`, expiry: 48–72 hrs), and emails the invite link to the doctor.
5. **Track Invitations:**
   - Admin views a list of all invitations with status: Pending / Accepted / Expired / Revoked.
   - Admin can **Resend** (generates a new token) or **Revoke** (invalidates the link) any pending/expired invite.
6. **View Doctors:**
   - Admin sees a list of all registered doctors with their profile info: name, specialty, qualification, years of experience, services, status (invited/registered/active/suspended).
   - Admin can view (not edit) each doctor's working hours/days.
   - Admin can override availability in exceptional cases (e.g., marking a doctor unavailable for an emergency).
7. **Operational Oversight:**
   - Admin views all appointments across all doctors: which patient booked with which doctor, date/time, and status.
   - Admin does **not** see prescriptions or clinical notes — that data stays restricted to doctor + patient only.
8. Admin can log out at any time; returning requires the same shared login page.

---

## 3. Doctor Flow (Step by Step)

### A. Onboarding (One-Time)
1. Admin sends an invitation to the doctor's email.
2. Doctor receives the invitation email containing a secure link (token-based) and a backup code.
3. Doctor clicks the link → the system verifies the token is valid and unexpired.
4. Doctor enters/confirms their email → sets a password.
5. System sends an **OTP** to the doctor's email.
6. Doctor enters the OTP → system verifies it.
7. **Registration page** opens → doctor enters core credentials: name, email, password (already partially filled from invite flow).
8. Immediately after, the **mandatory one-time profile form** appears, asking for:
   - Academic background / qualification
   - Specialty / domain
   - Years of experience
   - Services offered
   - Working hours and working days (initial availability)
9. Doctor submits the form → system creates the **doctor's workspace** → `doctorStatus` becomes `active`.
10. This form **cannot be re-filled** — all fields except working hours/days are locked from this point forward.

### B. Regular Login (After Onboarding)
1. Doctor opens the shared login page → enters email + password.
2. System verifies credentials → detects role = `doctor` → redirects to **Doctor Dashboard**.

### C. Day-to-Day Doctor Dashboard Flow
1. Doctor views **upcoming appointments** — patient name, time, reason for visit (if provided).
2. Doctor can view patient details, but only for patients with a confirmed/completed appointment relationship with them.
3. Doctor can **edit working hours/working days** at any time (only editable fields post-registration).
4. Doctor cannot delete/edit an availability slot that already has a booked appointment — must cancel/reschedule that appointment first.
5. After a consultation, doctor can **add a prescription** (medicines + notes) tied to that specific appointment — visible only to that patient and the doctor.
6. Doctor can mark an appointment as **Completed** or **No-Show**.
7. Doctor can **cancel** an appointment at any time if needed (patient gets notified).
8. Doctor logs out; returning requires the same shared login page.

---

## 4. Patient Flow (Step by Step)

### A. Registration (One-Time)
1. Patient visits the website's landing page.
2. Patient clicks "Sign Up" → fills in: name, phone, email, password, date of birth.
3. System sends an **OTP** to the patient's email.
4. Patient enters the OTP → system verifies it → account and **patient workspace** are created.

### B. Regular Login (After Registration)
1. Patient opens the shared login page → enters email + password.
2. System verifies credentials → detects role = `patient` → redirects to **Patient Dashboard**.

### C. Booking an Appointment
1. Patient browses doctor cards on the dashboard — each shows name, specialty, years of experience, and rating.
2. Patient clicks **"Book Appointment"** on a chosen doctor's card.
3. **Step 1 — Choose Slot:** Patient selects an available date and time from the doctor's schedule. Slot is temporarily held (5–10 min) to prevent double-booking.
4. **Step 2 — Patient Details:** Patient confirms/enters name, age (auto-calculated from DOB on file), and phone number.
5. **Step 3 — Confirm & Pay:** Patient reviews the fee, clicks "Confirm Booking," mock payment processes (always succeeds in Phase 1) → appointment status becomes `confirmed`.
6. Patient receives a confirmation (visible in dashboard; email confirmation optional).

### D. Managing Appointments
1. Patient can view **upcoming appointments** and **appointment history** on their dashboard.
2. Patient can **cancel or reschedule** an appointment up to 2 hours before the scheduled time.
3. After an appointment is marked **Completed** by the doctor, patient can:
   - View the **prescription** added by the doctor for that visit.
   - Leave a **review/rating** for that doctor (one review per appointment).
4. Patient logs out; returning requires the same shared login page.

---

## 5. Shared Login Logic (All Roles)

1. User (any role) lands on **one single login page**.
2. User enters email + password.
3. System validates credentials against the `User` table.
4. System checks the `role` field on the matched record.
5. Based on role, system redirects to:
   - `role = admin` → Admin Dashboard
   - `role = doctor` → Doctor Dashboard
   - `role = patient` → Patient Dashboard
6. No Google sign-in is used anywhere in this flow — email + password only, for all three roles.