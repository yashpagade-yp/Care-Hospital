import type {
  AdminDashboard,
  DayOfWeek,
  AdminProfile,
  Appointment,
  AppointmentListItem,
  AvailabilityType,
  DoctorAvailability,
  DoctorCard,
  DoctorDashboard,
  DoctorInvitation,
  DoctorProfile,
  PatientDashboard,
  PatientProfile,
  Payment,
  Prescription,
  Review,
  Session,
  UserSummary,
} from "@/types/domain";

const now = new Date();
const inDays = (days: number, hours = 10) =>
  new Date(now.getFullYear(), now.getMonth(), now.getDate() + days, hours, 0, 0).toISOString();

export const mockUsers: {
  patient: PatientProfile;
  doctor: DoctorProfile;
  admin: AdminProfile;
} = {
  patient: {
    id: "patient-101",
    name: "Aarav Patel",
    email: "patient@medcare.app",
    phone: "+91 98765 43210",
    role: "PATIENT",
    created_at: now.toISOString(),
    dob: "1997-08-14",
  },
  doctor: {
    id: "doctor-201",
    name: "Dr. Meera Khanna",
    email: "doctor@medcare.app",
    phone: "+91 98200 11002",
    role: "DOCTOR",
    created_at: now.toISOString(),
    qualification: "MD Internal Medicine",
    specialty: "Internal Medicine",
    experience_years: 11,
    services: ["General consultation", "Preventive care", "Chronic care follow-up"] as string[],
    doctor_status: "ACTIVE",
  },
  admin: {
    id: "admin-301",
    name: "Ritika Sharma",
    email: "admin@medcare.app",
    phone: "+91 98111 22003",
    role: "ADMIN",
    created_at: now.toISOString(),
  },
};

export const demoAccounts = [
  { email: "patient@medcare.app", password: "patient123", role: "PATIENT" },
  { email: "doctor@medcare.app", password: "doctor123", role: "DOCTOR" },
  { email: "admin@medcare.app", password: "admin123", role: "ADMIN" },
] as const;

export const doctorCards: DoctorCard[] = [
  {
    doctor_id: "doctor-201",
    name: "Dr. Meera Khanna",
    specialty: "Internal Medicine",
    experience_years: 11,
    rating: 4.8,
  },
  {
    doctor_id: "doctor-202",
    name: "Dr. Rohan Sen",
    specialty: "Cardiology",
    experience_years: 14,
    rating: 4.9,
  },
  {
    doctor_id: "doctor-203",
    name: "Dr. Aisha Menon",
    specialty: "Pediatrics",
    experience_years: 9,
    rating: 4.7,
  },
];

export const appointments: Appointment[] = [
  {
    id: "appt-001",
    patient_id: "patient-101",
    doctor_id: "doctor-201",
    doctor_name: "Dr. Meera Khanna",
    patient_name: "Aarav Patel",
    patient_phone: "+91 98765 43210",
    patient_age: 28,
    patient_gender: "Male",
    patient_blood_group: "B+",
    date_time: inDays(2, 11),
    status: "CONFIRMED",
    fee: 800,
    reason: "Recurring fatigue and sleep issues",
    payment_status: "PAID",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
  {
    id: "appt-002",
    patient_id: "patient-101",
    doctor_id: "doctor-202",
    doctor_name: "Dr. Rohan Sen",
    patient_name: "Aarav Patel",
    patient_phone: "+91 98765 43210",
    patient_age: 28,
    patient_gender: "Male",
    patient_blood_group: "B+",
    date_time: inDays(-6, 15),
    status: "COMPLETED",
    fee: 1500,
    reason: "Follow-up for chest discomfort",
    payment_status: "PAID",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
  {
    id: "appt-003",
    patient_id: "patient-104",
    doctor_id: "doctor-201",
    doctor_name: "Dr. Meera Khanna",
    patient_name: "Ishita Rao",
    patient_phone: "+91 98231 44010",
    patient_age: 34,
    patient_gender: "Female",
    patient_blood_group: "O+",
    date_time: inDays(1, 9),
    status: "CONFIRMED",
    fee: 800,
    reason: "Medication review",
    payment_status: "PAID",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
  {
    id: "appt-004",
    patient_id: "patient-105",
    doctor_id: "doctor-201",
    doctor_name: "Dr. Meera Khanna",
    patient_name: "Kabir Joshi",
    patient_phone: "+91 98989 11008",
    patient_age: 46,
    patient_gender: "Male",
    patient_blood_group: "A+",
    date_time: inDays(-1, 17),
    status: "NO_SHOW",
    fee: 800,
    reason: "Post-discharge consultation",
    payment_status: "PAID",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
];

export const payments: Payment[] = [
  {
    id: "pay-001",
    appointment_id: "appt-001",
    amount: 800,
    transaction_ref: "MOCK-APPT001",
    status: "SUCCESS",
    created_at: now.toISOString(),
  },
  {
    id: "pay-002",
    appointment_id: "appt-002",
    amount: 1500,
    transaction_ref: "MOCK-APPT002",
    status: "SUCCESS",
    created_at: now.toISOString(),
  },
];

export const prescriptions: Prescription[] = [
  {
    id: "rx-001",
    appointment_id: "appt-002",
    doctor_id: "doctor-202",
    doctor_name: "Dr. Rohan Sen",
    patient_id: "patient-101",
    patient_name: "Aarav Patel",
    patient_phone: "+91 98765 43210",
    patient_age: 28,
    patient_gender: "Male",
    patient_blood_group: "B+",
    visit_reason: "Follow-up for chest discomfort",
    medicines: ["Aspirin 75mg", "Atorvastatin 10mg"],
    notes: "Review in 30 days. Maintain low-salt diet and regular walking.",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
];

export const reviews: Review[] = [
  {
    id: "review-001",
    appointment_id: "appt-002",
    patient_id: "patient-101",
    doctor_id: "doctor-202",
    rating: 5,
    comment: "Very clear explanation and thoughtful follow-up guidance.",
    is_hidden: false,
    created_at: now.toISOString(),
  },
  {
    id: "review-002",
    appointment_id: "appt-006",
    patient_id: "patient-109",
    doctor_id: "doctor-201",
    rating: 2,
    comment: "Wait time was long and the tone felt rushed.",
    is_hidden: true,
    created_at: now.toISOString(),
  },
];

export const invitations: DoctorInvitation[] = [
  {
    id: "invite-001",
    doctor_email: "newdoctor@medcare.app",
    status: "PENDING",
    expires_at: inDays(2, 23),
    created_at: now.toISOString(),
  },
  {
    id: "invite-002",
    doctor_email: "cardio.consult@medcare.app",
    status: "ACCEPTED",
    expires_at: inDays(-3, 23),
    created_at: now.toISOString(),
  },
];

export const availabilities: DoctorAvailability[] = [
  {
    id: "avail-001",
    doctor_id: "doctor-201",
    availability_type: "RECURRING",
    day_of_week: "MONDAY",
    start_time: "09:00:00",
    end_time: "13:00:00",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
  {
    id: "avail-002",
    doctor_id: "doctor-201",
    availability_type: "RECURRING",
    day_of_week: "WEDNESDAY",
    start_time: "14:00:00",
    end_time: "18:00:00",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
  {
    id: "avail-003",
    doctor_id: "doctor-201",
    availability_type: "EXCEPTION_BLOCKED",
    exception_date: inDays(3).slice(0, 10),
    start_time: "10:00:00",
    end_time: "12:00:00",
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  },
];

export const patientDashboard: PatientDashboard = {
  profile: mockUsers.patient,
  doctor_cards: doctorCards,
  upcoming_appointments: appointments.filter((item) => item.patient_id === mockUsers.patient.id && item.status === "CONFIRMED"),
  appointment_history: appointments.filter((item) => item.patient_id === mockUsers.patient.id && item.status !== "CONFIRMED"),
};

export const doctorDashboard: DoctorDashboard = {
  profile: mockUsers.doctor,
  upcoming_appointments: appointments.filter((item) => item.doctor_id === mockUsers.doctor.id && item.status === "CONFIRMED"),
  appointment_history: appointments.filter((item) => item.doctor_id === mockUsers.doctor.id && item.status !== "CONFIRMED"),
};

export const adminDashboard: AdminDashboard = {
  profile: mockUsers.admin,
  doctor_count: 12,
  patient_count: 2,
  invitation_count: invitations.length,
  appointment_count: appointments.length,
  recent_invitations: invitations,
  recent_appointments: appointments.slice(0, 3),
  flagged_reviews: reviews.filter((review) => review.is_hidden),
};

export const doctorDirectory: DoctorProfile[] = [
  mockUsers.doctor,
  {
    id: "doctor-202",
    name: "Dr. Rohan Sen",
    email: "rohan.sen@medcare.app",
    phone: "+91 98451 10203",
    role: "DOCTOR",
    created_at: now.toISOString(),
    qualification: "DM Cardiology",
    specialty: "Cardiology",
    experience_years: 14,
    services: ["Heart rhythm review", "Cardiac follow-up", "Preventive heart screening"],
    doctor_status: "ACTIVE",
  },
  {
    id: "doctor-203",
    name: "Dr. Aisha Menon",
    email: "aisha.menon@medcare.app",
    phone: "+91 98843 10244",
    role: "DOCTOR",
    created_at: now.toISOString(),
    qualification: "MD Pediatrics",
    specialty: "Pediatrics",
    experience_years: 9,
    services: ["Child wellness checks", "Vaccination review", "Growth monitoring"],
    doctor_status: "REGISTERED",
  },
];

export const patientDirectory: UserSummary[] = [
  mockUsers.patient,
  {
    id: "patient-104",
    name: "Ishita Rao",
    email: "ishita.rao@medcare.app",
    phone: "+91 98231 44010",
    role: "PATIENT",
    created_at: now.toISOString(),
  },
];

export function createDemoSession(role: Session["role"]): Session {
  if (role === "PATIENT") {
    return {
      token: "demo-patient-token",
      role,
      user: mockUsers.patient,
    };
  }

  if (role === "DOCTOR") {
    return {
      token: "demo-doctor-token",
      role,
      user: mockUsers.doctor,
    };
  }

  return {
    token: "demo-admin-token",
    role,
    user: mockUsers.admin,
  };
}

export function listPatientAppointments(patientId: string): AppointmentListItem[] {
  return appointments.filter((item) => item.patient_id === patientId);
}

export function listDoctorAppointments(doctorId: string): AppointmentListItem[] {
  return appointments.filter((item) => item.doctor_id === doctorId);
}
