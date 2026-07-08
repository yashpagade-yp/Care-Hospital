import {
  adminDashboard,
  appointments,
  availabilities,
  doctorDashboard,
  doctorDirectory,
  invitations,
  listDoctorAppointments,
  listPatientAppointments,
  patientDashboard,
  patientDirectory,
  prescriptions,
  reviews,
} from "@/lib/mock/data";
import {
  appointmentApi,
  availabilityApi,
  dashboardApi,
  invitationApi,
  paymentApi,
  prescriptionApi,
  reviewApi,
  userApi,
} from "@/lib/api/endpoints";
import type { Appointment, Session } from "@/types/domain";

export async function loadPatientDashboard() {
  try {
    return await dashboardApi.patient();
  } catch {
    return patientDashboard;
  }
}

export async function loadDoctorDashboard() {
  try {
    return await dashboardApi.doctor();
  } catch {
    return doctorDashboard;
  }
}

export async function loadAdminDashboard() {
  try {
    return await dashboardApi.admin();
  } catch {
    return adminDashboard;
  }
}

export async function loadDoctorDirectory() {
  try {
    const response = await userApi.listDoctors();
    return response.items;
  } catch {
    return doctorDirectory;
  }
}

export async function loadPatientDirectory() {
  try {
    const response = await userApi.listPatients();
    return response.items;
  } catch {
    return patientDirectory;
  }
}

export async function loadInvitations() {
  try {
    const response = await invitationApi.list();
    return response.invitations;
  } catch {
    return invitations;
  }
}

export async function loadPatientAppointments(patientId: string) {
  try {
    const response = await appointmentApi.listPatientAppointments(patientId);
    return response.items;
  } catch {
    return listPatientAppointments(patientId);
  }
}

export async function loadDoctorAppointments(doctorId: string) {
  try {
    const response = await appointmentApi.listDoctorAppointments(doctorId);
    return response.items;
  } catch {
    return listDoctorAppointments(doctorId);
  }
}

export async function loadAdminAppointments() {
  try {
    const response = await appointmentApi.listAdminAppointments();
    return response.items;
  } catch {
    return appointments;
  }
}

export async function loadPrescriptionsForPatient(patientId: string) {
  try {
    const response = await prescriptionApi.listForPatient(patientId);
    return response.items;
  } catch {
    return prescriptions.filter((item) => item.patient_id === patientId);
  }
}

export async function loadPrescriptionsForDoctor(doctorId: string) {
  try {
    const response = await prescriptionApi.listForDoctor(doctorId);
    return response.items;
  } catch {
    return prescriptions.filter((item) => item.doctor_id === doctorId);
  }
}

export async function loadDoctorReviews(doctorId: string, includeHidden = false) {
  try {
    const response = includeHidden
      ? await reviewApi.listDoctorReviewsForAdmin(doctorId)
      : await reviewApi.listDoctorReviews(doctorId);
    return response.items;
  } catch {
    return reviews.filter((item) => item.doctor_id === doctorId && (includeHidden || !item.is_hidden));
  }
}

export async function loadDoctorAvailability(doctorId: string) {
  try {
    const response = await availabilityApi.listDoctorAvailability(doctorId);
    return response.items;
  } catch {
    return availabilities.filter((item) => item.doctor_id === doctorId);
  }
}

export async function loadPaymentByAppointment(appointmentId: string) {
  try {
    return await paymentApi.getPaymentByAppointment(appointmentId);
  } catch {
    return null;
  }
}

export function canAccessRoleRoute(session: Session | null, allowedRole: Session["role"]) {
  return session?.role === allowedRole;
}

export function findAppointmentById(appointmentId: string): Appointment | null {
  return appointments.find((item) => item.id === appointmentId) ?? null;
}
