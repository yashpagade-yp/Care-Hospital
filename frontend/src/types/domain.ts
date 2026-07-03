export type UserRole = "PATIENT" | "DOCTOR" | "ADMIN";
export type DoctorStatus = "REGISTERED" | "ACTIVE" | "SUSPENDED";
export type OtpPurpose =
  | "DOCTOR_INVITE_VERIFY"
  | "PATIENT_REGISTER_VERIFY"
  | "PASSWORD_RESET_VERIFY"
  | "LOGIN_VERIFY";
export type AppointmentStatus =
  | "CONFIRMED"
  | "COMPLETED"
  | "CANCELLED"
  | "NO_SHOW"
  | "RESCHEDULED";
export type PaymentStatus = "PAID" | "REFUNDED";
export type CancelledBy = "PATIENT" | "DOCTOR";
export type InvitationStatus = "PENDING" | "ACCEPTED" | "EXPIRED" | "REVOKED";
export type AvailabilityType =
  | "RECURRING"
  | "EXCEPTION_AVAILABLE"
  | "EXCEPTION_BLOCKED";
export type DayOfWeek =
  | "MONDAY"
  | "TUESDAY"
  | "WEDNESDAY"
  | "THURSDAY"
  | "FRIDAY"
  | "SATURDAY"
  | "SUNDAY";

export type UserSummary = {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  role: UserRole;
  created_at?: string | null;
};

export type PatientProfile = UserSummary & {
  dob?: string | null;
};

export type DoctorProfile = UserSummary & {
  qualification?: string | null;
  specialty?: string | null;
  experience_years?: number | null;
  consultation_fee?: number | null;
  services: string[];
  doctor_status?: DoctorStatus | null;
};

export type AdminProfile = UserSummary;

export type LoginResponse = {
  access_token: string;
  token_type: string;
  role: UserRole;
  user: UserSummary;
};

export type OtpSentResponse = {
  message: string;
  email: string;
  purpose: OtpPurpose;
};

export type PasswordResetResponse = {
  message: string;
};

export type DoctorCard = {
  doctor_id: string;
  name: string;
  specialty?: string | null;
  experience_years?: number | null;
  rating?: number | null;
};

export type AppointmentListItem = {
  id: string;
  patient_id: string;
  doctor_id: string;
  date_time: string;
  status: AppointmentStatus;
  fee: number;
};

export type Appointment = AppointmentListItem & {
  reason?: string | null;
  payment_status: PaymentStatus;
  cancelled_by?: CancelledBy | null;
  cancel_reason?: string | null;
  rescheduled_to_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type Payment = {
  id: string;
  appointment_id: string;
  amount: number;
  transaction_ref: string;
  status: "SUCCESS" | "REFUNDED";
  created_at?: string | null;
};

export type AppointmentConfirmation = {
  appointment: Appointment;
  payment: Payment;
  patient_name?: string | null;
  doctor_name?: string | null;
};

export type AppointmentReschedule = {
  previous_appointment: Appointment;
  new_appointment: Appointment;
};

export type Prescription = {
  id: string;
  appointment_id: string;
  doctor_id: string;
  patient_id: string;
  medicines: string[];
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type Review = {
  id: string;
  appointment_id: string;
  patient_id: string;
  doctor_id: string;
  rating: number;
  comment?: string | null;
  is_hidden: boolean;
  created_at: string;
};

export type DoctorInvitation = {
  id: string;
  doctor_email: string;
  status: InvitationStatus;
  expires_at: string;
  created_at: string;
};

export type DoctorAvailability = {
  id: string;
  doctor_id: string;
  availability_type: AvailabilityType;
  day_of_week?: DayOfWeek | null;
  start_time: string;
  end_time: string;
  exception_date?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PatientDashboard = {
  profile: PatientProfile;
  doctor_cards: DoctorCard[];
  upcoming_appointments: AppointmentListItem[];
  appointment_history: AppointmentListItem[];
};

export type DoctorDashboard = {
  profile: DoctorProfile;
  upcoming_appointments: AppointmentListItem[];
  appointment_history: AppointmentListItem[];
};

export type AdminDashboard = {
  profile: AdminProfile;
  doctor_count: number;
  invitation_count: number;
  appointment_count: number;
  recent_invitations: DoctorInvitation[];
  recent_appointments: AppointmentListItem[];
  flagged_reviews: Review[];
};

export type Session = {
  token: string;
  role: UserRole;
  user: UserSummary;
};
