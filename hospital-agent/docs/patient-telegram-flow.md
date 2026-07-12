# Patient Telegram Flow

## Purpose

This document explains the current patient-facing Telegram chatbot flow for Care Hospital.

The Telegram bot is mainly used for:
- booking appointments
- viewing available doctors
- checking doctor availability
- helping registered patients access protected records such as prescriptions
- answering general hospital-related questions
- responding in English, Hindi, or Marathi based on the patient's language

The backend remains the source of truth for doctors, appointments, prescriptions, authentication, and authorization.

## Flow 1: Existing Patient Wants Prescription

This flow is for a patient who is already registered in the hospital system and wants to view prescription-related information.

1. Patient opens the Telegram bot.
2. Patient asks to view prescription or previous medical record.
3. Bot identifies that this is protected patient-specific data.
4. Bot tells the patient:

   ```text
   You are an existing patient. Please log in.
   ```

5. Patient provides registered email and password.
6. Backend sends OTP to the patient's registered email.
7. Patient enters OTP in Telegram.
8. Backend verifies OTP and creates an authenticated patient session.
9. Bot fetches prescriptions from the backend using the authenticated patient session.
10. Bot shows only the prescriptions that belong to that patient.

Important rules:
- Prescription viewing requires login.
- The Telegram bot must not expose prescription data without backend authentication.
- The bot does not create or modify prescriptions.
- The bot only shows prescriptions that already exist in backend records.

## Flow 2: Appointment Booking For New Or Registered Patient

This flow is for appointment booking from Telegram.

Appointment booking does not require patient registration first. A new patient can book directly as a Telegram guest. A registered patient can also book through the same Telegram booking flow.

1. Patient opens the Telegram bot.
2. Patient asks to book an appointment.
3. Bot understands whether the patient requested all doctors, a particular specialty, or a doctor related to a need such as skin care, bone care, or general medicine.
4. Bot shows only the relevant doctors. It shows the complete list only when the patient asks for all doctors.
5. Patient chooses a doctor by number, name, or specialty.
6. If booking starts after a specialty search, the bot keeps that filtered doctor list instead of showing every doctor again.
7. Bot shows the selected doctor's available timings and asks for the preferred date and time.
8. Patient provides the preferred date and time.
9. Bot checks the selected doctor's availability through the backend.
10. Bot asks for patient details such as:
   - name
   - age
   - phone number
   - reason for visit
11. Bot sends the appointment booking request to the backend.
12. Backend creates the appointment for the selected doctor.
13. Bot sends appointment confirmation to the patient.
14. The appointment becomes visible in the selected doctor's dashboard.

Important rules:
- New patients can book appointments without registration.
- Registered patients can also book appointments through Telegram.
- Appointment truth stays in the backend.
- The Telegram bot must not bypass backend availability or booking rules.
- Doctor dashboards should show Telegram-created appointments for the correct doctor.

## Language And Conversation Behaviour

The patient can communicate in English, Hindi, or Marathi.

1. The bot detects the language used in the patient's message.
2. It responds in the same language.
3. It remembers the language during an active flow so follow-up questions remain consistent.
4. Translation preserves doctor and medicine names, dates, times, OTPs, emails, phone numbers, IDs, and Telegram commands.

The conversation should be natural, clear, respectful, and patient-friendly. The bot may answer general questions about hospital services, symptoms, specialties, doctors, availability, timings, registration, login, prescriptions, and appointments. It must not diagnose conditions, prescribe medicine, or replace professional medical advice.

## Specialty-Based Doctor Search

The bot supports focused doctor discovery.

```text
Patient: Show me doctors for skin care.
Bot: I found these Dermatology doctors for you: ...
Patient: Book an appointment.
Bot: Here are the available timings for the Dermatology doctor you selected: ...
```

The same pattern applies to supported needs and specialties such as general medicine, orthopedics, dermatology, pediatrics, cardiology, neurology, gynecology, ENT, and ophthalmology.

Important rules:
- A focused request returns only matching doctors.
- A booking request continues with the currently filtered doctor options.
- The complete doctor list is returned when the patient explicitly asks for all doctors.
- Availability and appointment booking are always validated by the backend.

## Summary

Appointment booking is open to both new and registered patients through Telegram.

Prescription viewing is protected and requires an existing registered patient login with OTP verification.

The bot supports natural conversations in English, Hindi, and Marathi and can narrow doctor results according to the patient's requested specialty or need.
