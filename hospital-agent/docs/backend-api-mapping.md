# Hospital Agent Backend API Mapping

## Purpose
This document maps the existing hospital backend APIs that the `hospital-agent` can safely use for V1 patient flows.

The backend remains the source of truth.
The hospital agent must only orchestrate these APIs and must not replace backend business logic.

## V1 Scope Covered
- Check doctor availability
- Book appointment
- Reschedule appointment
- Cancel appointment
- Read doctor list for appointment selection
- Read patient appointments for follow-up actions

## Telegram And Backend Boundary

- A Telegram bot is the message entry point for the hospital agent.
- The Telegram bot token enables Telegram communication only.
- The bot token must not be treated as hospital authentication.
- A user may start a chat with the hospital on Telegram before any protected backend action happens.
- Patient-specific actions such as appointment lookup, booking, cancellation, and rescheduling must still respect backend authentication and verification requirements.
- The hospital agent should separate:
  - open conversation or FAQ guidance
  - protected backend actions tied to patient identity

## Auth Model

### Login Flow
The backend uses a two-step login flow for all roles.

1. `POST /v1/auth/login`
   - validates email + password
   - sends login OTP to email
   - does not return a token yet

2. `POST /v1/auth/verify-login-otp`
   - validates OTP
   - returns JWT bearer token

References:
- [auth_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/auth_router.py:24)
- [auth_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/auth_controller.py:35)

### Token Usage
Protected APIs use bearer token auth.
The token payload contains:
- `user_role`
- `id`
- `expires`

References:
- [router_dependencies.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/router_dependencies.py:15)
- [auth.py](/C:/Users/yash/my_hospital/backend/commons/auth.py:18)

## Doctor Discovery

### List Doctors
- Method: `GET`
- Endpoint: `/v1/doctors`
- Access: authenticated `PATIENT`, `DOCTOR`, `ADMIN`
- Use in hospital-agent:
  - help patient select a doctor
  - show doctor name, specialty, services, experience, status

Reference:
- [user_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/user_router.py:320)

## Availability APIs

### List Doctor Availability
- Method: `GET`
- Endpoint: `/v1/doctors/{doctor_id}/availability`
- Access: authenticated `PATIENT`, `DOCTOR`, `ADMIN`
- Response: recurring and exception availability entries for the doctor
- Use in hospital-agent:
  - show available schedule structure
  - combine with booked slots to infer candidate appointment times

Reference:
- [availability_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/availability_router.py:164)

### Availability Response Notes
Important fields:
- `availability_type`
- `day_of_week`
- `start_time`
- `end_time`
- `exception_date`

Times are returned as strings like `HH:MM`.
Exception dates are returned as `YYYY-MM-DD`.

Reference:
- [availability_response_schema.py](/C:/Users/yash/my_hospital/backend/core/apis/schemas/responses_schemas/availability_response_schema.py:9)

### Booked Slots For Doctor
- Method: `GET`
- Endpoint: `/v1/doctors/{doctor_id}/booked-slots`
- Access: authenticated `PATIENT`, `DOCTOR`, `ADMIN`
- Response: list of booked slot datetimes
- Use in hospital-agent:
  - remove already-occupied slots from candidate availability
  - avoid exposing other patients' details

Reference:
- [appointment_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/appointment_router.py:431)

## Appointment Booking APIs

### Step 1: Create Slot Hold
- Method: `POST`
- Endpoint: `/v1/appointments/slot-holds`
- Access: authenticated `PATIENT`
- Request body:
  - `doctor_id`
  - `date_time`
- Response:
  - `id`
  - `patient_id`
  - `doctor_id`
  - `date_time`
  - `expires_at`

Use in hospital-agent:
- reserve a slot temporarily before final confirmation

Important backend rules:
- patient must exist and be OTP verified
- doctor must exist and be `ACTIVE`
- slot must be in the future
- slot must match doctor availability
- slot cannot already be held
- slot cannot already be booked
- hold expires after 10 minutes

References:
- [appointment_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/appointment_router.py:37)
- [appointment_request_schema.py](/C:/Users/yash/my_hospital/backend/core/apis/schemas/request_schemas/appointment_request_schema.py:11)
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:36)

### Step 2: Confirm Appointment
- Method: `POST`
- Endpoint: `/v1/appointments/confirm`
- Access: authenticated `PATIENT`
- Request body:
  - `slot_hold_id`
  - `patient_name`
  - `patient_phone`
  - `patient_age`
  - `patient_gender`
  - `patient_blood_group` optional
  - `reason` optional
  - `fee`
- Response:
  - confirmed appointment object
  - payment object
  - `patient_name`
  - `doctor_name`

Use in hospital-agent:
- finalize booking after collecting missing booking details from patient

Important backend rules:
- hold must exist
- hold must belong to authenticated patient
- hold must not be expired
- slot still must not already be booked
- booking uses mock payment and marks `payment_status = PAID`

References:
- [appointment_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/appointment_router.py:83)
- [appointment_request_schema.py](/C:/Users/yash/my_hospital/backend/core/apis/schemas/request_schemas/appointment_request_schema.py:20)
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:106)

## Appointment Management APIs

### List Patient Appointments
- Method: `GET`
- Endpoint: `/v1/patients/{patient_id}/appointments`
- Access:
  - same patient
  - `ADMIN`
- Use in hospital-agent:
  - show patient upcoming appointments
  - identify appointment ID before cancel/reschedule

Reference:
- [appointment_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/appointment_router.py:293)

### Cancel Appointment
- Method: `PATCH`
- Endpoint: `/v1/appointments/{appointment_id}/cancel`
- Access:
  - owning `PATIENT`
  - owning `DOCTOR`
- Request body:
  - `cancel_reason`
- Response:
  - updated appointment object

Use in hospital-agent:
- cancel a patient appointment after confirmation

Important backend rules:
- patient can only cancel their own appointment
- doctor can only cancel their own appointment
- patient can cancel only up to 2 hours before appointment time
- appointment cannot already be `CANCELLED`, `RESCHEDULED`, `COMPLETED`, or `NO_SHOW`
- cancellation triggers payment refund state

References:
- [appointment_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/appointment_router.py:129)
- [appointment_request_schema.py](/C:/Users/yash/my_hospital/backend/core/apis/schemas/request_schemas/appointment_request_schema.py:58)
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:207)
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:741)

### Reschedule Appointment
- Method: `PATCH`
- Endpoint: `/v1/appointments/{appointment_id}/reschedule`
- Access:
  - owning `PATIENT`
  - owning `DOCTOR`
- Request body:
  - `new_date_time`
  - `reason` optional
- Response:
  - `previous_appointment`
  - `new_appointment`

Use in hospital-agent:
- move appointment to another valid slot

Important backend rules:
- patient can reschedule only up to 2 hours before appointment time
- new slot must be in the future
- new slot must match doctor availability
- new slot must not already be booked
- original appointment becomes `RESCHEDULED`
- new appointment is created as a separate record

References:
- [appointment_router.py](/C:/Users/yash/my_hospital/backend/core/apis/routers/appointment_router.py:184)
- [appointment_request_schema.py](/C:/Users/yash/my_hospital/backend/core/apis/schemas/request_schemas/appointment_request_schema.py:66)
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:279)
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:741)

## Backend Rules The Agent Must Respect

### Patient Verification
Booking requires the patient account to be OTP verified.

Reference:
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:626)

### Doctor Must Be Active
The selected doctor must exist and have `doctor_status = ACTIVE`.

Reference:
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:651)

### Patient 2-Hour Restriction
Patients can cancel or reschedule only up to 2 hours before the appointment.

Reference:
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:741)

### Availability Logic
The backend checks:
- exception blocked slots first
- exception available slots next
- recurring weekly slots after that

The agent should not re-implement this logic.
The agent should only send requested datetime values and let the backend enforce availability.

Reference:
- [appointment_controller.py](/C:/Users/yash/my_hospital/backend/core/controllers/appointment_controller.py:775)

## Recommended V1 Agent Flow

### Check Availability
1. authenticate patient
2. list doctors if doctor not chosen yet
3. read doctor availability
4. read doctor booked slots
5. present candidate times to patient

### Book Appointment
1. authenticate patient
2. collect `doctor_id` and desired datetime
3. create slot hold
4. collect missing booking fields
5. confirm appointment
6. send confirmation back on Telegram

### Cancel Appointment
1. authenticate patient
2. list patient appointments
3. confirm which appointment to cancel
4. send cancel request with reason
5. return backend result

### Reschedule Appointment
1. authenticate patient
2. list patient appointments
3. identify target appointment
4. collect new desired datetime
5. send reschedule request
6. return old/new appointment result

## FAQ Note
No dedicated FAQ backend endpoint was identified in the current backend route layer.

For V1, hospital FAQs should likely be handled by:
- prompt-based static hospital information
- curated local FAQ content inside `hospital-agent`

If backend-backed FAQs are needed later, that should be added as a separate backend capability.

## Current Implementation Direction
- Do not assume Docker-based setup for the current hospital-agent phase.
- Keep the Telegram integration path simple first.
- Add deployment packaging concerns later, after the Telegram and backend orchestration flow is stable.
