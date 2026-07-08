import { apiRequest } from "@/lib/api/client";
import type {
  AdminDashboard,
  Appointment,
  AppointmentConfirmation,
  AppointmentReschedule,
  BookedSlotList,
  DoctorAvailability,
  DoctorDashboard,
  DoctorInvitation,
  DoctorProfile,
  LoginResponse,
  OtpSentResponse,
  PasswordResetResponse,
  PatientDashboard,
  PatientProfile,
  Payment,
  Prescription,
  Review,
} from "@/types/domain";

type ListResponse<T> = { items: T[] };

export const authApi = {
  login: (payload: { email: string; password: string }) =>
    apiRequest<OtpSentResponse>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  verifyLoginOtp: (payload: { email: string; otp: string }) =>
    apiRequest<LoginResponse>("/v1/auth/verify-login-otp", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resendOtp: (payload: { email: string; purpose: string }) =>
    apiRequest<OtpSentResponse>("/v1/auth/resend-otp", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  forgotPassword: (payload: { email: string }) =>
    apiRequest<OtpSentResponse>("/v1/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  verifyPasswordResetOtp: (payload: { email: string; otp: string }) =>
    apiRequest<PasswordResetResponse>("/v1/auth/verify-password-reset-otp", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  resetPassword: (payload: { email: string; otp: string; new_password: string }) =>
    apiRequest<PasswordResetResponse>("/v1/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export const userApi = {
  registerPatient: (payload: {
    name: string;
    phone: string;
    email: string;
    password: string;
  }) =>
    apiRequest<PatientProfile>("/v1/patients/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  verifyPatientOtp: (payload: { email: string; otp: string }) =>
    apiRequest<PatientProfile>("/v1/patients/verify-otp", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  setDoctorCredentials: (payload: { token: string; email: string; password: string }) =>
    apiRequest<DoctorProfile>("/v1/doctors/set-credentials", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  verifyDoctorOtp: (payload: { email: string; otp: string }) =>
    apiRequest<DoctorProfile>("/v1/doctors/verify-otp", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  completeDoctorProfile: (payload: {
    name: string;
    email: string;
    qualification: string;
    specialty: string;
    experience_years: number;
    services: string[];
    working_slots: Array<{
      day_of_week: string;
      start_time: string;
      end_time: string;
    }>;
  }) =>
    apiRequest<DoctorProfile>("/v1/doctors/complete-profile", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getMyProfile: () =>
    apiRequest<PatientProfile | DoctorProfile | DoctorProfile>("/v1/users/me"),
  listDoctors: () => apiRequest<{ items: DoctorProfile[] }>("/v1/doctors"),
  listPatients: () => apiRequest<{ items: PatientProfile[] }>("/v1/patients"),
  deleteDoctor: (doctorId: string) =>
    apiRequest<{ message: string }>(`/v1/admin/doctors/${doctorId}`, {
      method: "DELETE",
    }),
  suspendDoctor: (doctorId: string) =>
    apiRequest<DoctorProfile>(`/v1/admin/doctors/${doctorId}/suspend`, {
      method: "PATCH",
    }),
};

export const invitationApi = {
  validate: (payload: { token: string }) =>
    apiRequest<{ valid: boolean; doctor_email?: string | null; expires_at?: string | null; status?: string | null }>(
      "/v1/invitations/validate",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),
  create: (payload: { doctor_email: string }) =>
    apiRequest<DoctorInvitation>("/v1/admin/invitations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  list: () => apiRequest<{ invitations: DoctorInvitation[] }>("/v1/admin/invitations"),
  resend: (payload: { invitation_id: string }) =>
    apiRequest<DoctorInvitation>("/v1/admin/invitations/resend", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  revoke: (payload: { invitation_id: string }) =>
    apiRequest<{ message: string }>("/v1/admin/invitations/revoke", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export const dashboardApi = {
  patient: () => apiRequest<PatientDashboard>("/v1/patient-dashboard"),
  doctor: () => apiRequest<DoctorDashboard>("/v1/doctor-dashboard"),
  admin: () => apiRequest<AdminDashboard>("/v1/admin-dashboard"),
};

export const appointmentApi = {
  createSlotHold: (payload: { doctor_id: string; date_time: string }) =>
    apiRequest<{ id: string; expires_at: string; doctor_id: string; patient_id: string; date_time: string }>(
      "/v1/appointments/slot-holds",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),
  confirm: (payload: {
    slot_hold_id: string;
    patient_name: string;
    patient_phone: string;
    patient_age: number;
    patient_gender: string;
    patient_blood_group?: string;
    reason?: string;
    fee: number;
  }) =>
    apiRequest<AppointmentConfirmation>("/v1/appointments/confirm", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  cancel: (appointmentId: string, payload: { cancel_reason: string }) =>
    apiRequest<Appointment>(`/v1/appointments/${appointmentId}/cancel`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  reschedule: (
    appointmentId: string,
    payload: { new_date_time: string; reason?: string },
  ) =>
    apiRequest<AppointmentReschedule>(`/v1/appointments/${appointmentId}/reschedule`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  updateStatus: (appointmentId: string, payload: { status: string }) =>
    apiRequest<Appointment>(`/v1/appointments/${appointmentId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listPatientAppointments: (patientId: string) =>
    apiRequest<ListResponse<Appointment>>(`/v1/patients/${patientId}/appointments`),
  listDoctorAppointments: (doctorId: string) =>
    apiRequest<ListResponse<Appointment>>(`/v1/doctors/${doctorId}/appointments`),
  listDoctorBookedSlots: (doctorId: string) =>
    apiRequest<BookedSlotList>(`/v1/doctors/${doctorId}/booked-slots`),
  listAdminAppointments: () =>
    apiRequest<ListResponse<Appointment>>("/v1/admin/appointments"),
  getAppointmentDetail: (appointmentId: string) =>
    apiRequest<{ appointment: Appointment; patient_name?: string | null; doctor_name?: string | null }>(
      `/v1/appointments/${appointmentId}`,
    ),
};

export const availabilityApi = {
  listDoctorAvailability: (doctorId: string) =>
    apiRequest<ListResponse<DoctorAvailability>>(`/v1/doctors/${doctorId}/availability`),
  createDoctorAvailability: (payload: {
    availability_type: string;
    day_of_week?: string;
    start_time: string;
    end_time: string;
    exception_date?: string;
  }) =>
    apiRequest<DoctorAvailability>("/v1/doctors/availability", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDoctorAvailability: (
    availabilityId: string,
    payload: {
      start_time?: string;
      end_time?: string;
      day_of_week?: string;
      exception_date?: string;
    },
  ) =>
    apiRequest<DoctorAvailability>(`/v1/doctors/availability/${availabilityId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  createAdminOverride: (payload: {
    doctor_id: string;
    availability_type: string;
    start_time: string;
    end_time: string;
    exception_date: string;
    reason?: string;
  }) =>
    apiRequest<DoctorAvailability>("/v1/admin/availability/overrides", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteAvailability: (availabilityId: string) =>
    apiRequest<void>(`/v1/doctors/availability/${availabilityId}`, { method: "DELETE" }),
};

export const reviewApi = {
  createReview: (payload: { appointment_id: string; rating: number; comment?: string }) =>
    apiRequest<Review>("/v1/patients/reviews", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listDoctorReviews: (doctorId: string) =>
    apiRequest<ListResponse<Review>>(`/v1/doctors/${doctorId}/reviews`),
  listDoctorReviewsForAdmin: (doctorId: string) =>
    apiRequest<ListResponse<Review>>(`/v1/admin/doctors/${doctorId}/reviews`),
  setReviewVisibility: (reviewId: string, payload: { is_hidden: boolean }) =>
    apiRequest<Review>(`/v1/admin/reviews/${reviewId}/visibility`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};

export const prescriptionApi = {
  createPrescription: (payload: {
    appointment_id: string;
    medicines: string[];
    notes?: string;
  }) =>
    apiRequest<Prescription>("/v1/doctors/prescriptions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updatePrescription: (
    prescriptionId: string,
    payload: { medicines: string[]; notes?: string },
  ) =>
    apiRequest<Prescription>(`/v1/doctors/prescriptions/${prescriptionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  getByAppointment: (appointmentId: string) =>
    apiRequest<Prescription>(`/v1/appointments/${appointmentId}/prescription`),
  listForPatient: (patientId: string) =>
    apiRequest<ListResponse<Prescription>>(`/v1/patients/${patientId}/prescriptions`),
  listForDoctor: (doctorId: string) =>
    apiRequest<ListResponse<Prescription>>(`/v1/doctors/${doctorId}/prescriptions`),
};

export const paymentApi = {
  createMockPayment: (payload: { appointment_id: string; amount: number }) =>
    apiRequest<Payment>("/v1/admin/payments/mock", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getPaymentByAppointment: (appointmentId: string) =>
    apiRequest<Payment>(`/v1/admin/appointments/${appointmentId}/payment`),
};
