import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { ProtectedRoute } from "@/components/routing/ProtectedRoute";
import { AdminDashboardPage } from "@/features/dashboard/pages/AdminDashboardPage";
import { AdminAppointmentsPage } from "@/features/dashboard/pages/AdminAppointmentsPage";
import { AdminDoctorsPage } from "@/features/dashboard/pages/AdminDoctorsPage";
import { AdminInvitationsPage } from "@/features/dashboard/pages/AdminInvitationsPage";
import { AdminOverridesPage } from "@/features/dashboard/pages/AdminOverridesPage";
import { AdminReviewsPage } from "@/features/dashboard/pages/AdminReviewsPage";
import { DoctorDashboardPage } from "@/features/dashboard/pages/DoctorDashboardPage";
import { DoctorAppointmentsPage } from "@/features/dashboard/pages/DoctorAppointmentsPage";
import { DoctorAvailabilityPage } from "@/features/dashboard/pages/DoctorAvailabilityPage";
import { DoctorPrescriptionsPage } from "@/features/dashboard/pages/DoctorPrescriptionsPage";
import { PatientDashboardPage } from "@/features/dashboard/pages/PatientDashboardPage";
import { PatientAppointmentsPage } from "@/features/dashboard/pages/PatientAppointmentsPage";
import { PatientPrescriptionsPage } from "@/features/dashboard/pages/PatientPrescriptionsPage";
import { PatientReviewsPage } from "@/features/dashboard/pages/PatientReviewsPage";
import { DoctorCredentialsPage } from "@/features/doctor-onboarding/pages/DoctorCredentialsPage";
import { DoctorInviteValidationPage } from "@/features/doctor-onboarding/pages/DoctorInviteValidationPage";
import { DoctorProfileSetupPage } from "@/features/doctor-onboarding/pages/DoctorProfileSetupPage";
import { DoctorVerifyOtpPage } from "@/features/doctor-onboarding/pages/DoctorVerifyOtpPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { AppointmentBookingPage } from "@/features/patient/pages/AppointmentBookingPage";
import { ForgotPasswordPage } from "@/features/auth/pages/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { PatientRegisterPage } from "@/features/auth/pages/PatientRegisterPage";
import { PatientVerifyOtpPage } from "@/features/auth/pages/PatientVerifyOtpPage";
import { ResetPasswordPage } from "@/features/auth/pages/ResetPasswordPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "patient/register", element: <PatientRegisterPage /> },
      { path: "patient/verify-otp", element: <PatientVerifyOtpPage /> },
      { path: "auth/forgot-password", element: <ForgotPasswordPage /> },
      { path: "auth/reset-password", element: <ResetPasswordPage /> },
      { path: "doctor/invite", element: <DoctorInviteValidationPage /> },
      { path: "doctor/set-credentials", element: <DoctorCredentialsPage /> },
      { path: "doctor/verify-otp", element: <DoctorVerifyOtpPage /> },
      { path: "doctor/complete-profile", element: <DoctorProfileSetupPage /> },
      {
        element: <ProtectedRoute allowedRoles={["PATIENT"]} />,
        children: [
          { path: "patient/book", element: <AppointmentBookingPage /> },
          { path: "patient/dashboard", element: <PatientDashboardPage /> },
          { path: "patient/appointments", element: <PatientAppointmentsPage /> },
          { path: "patient/prescriptions", element: <PatientPrescriptionsPage /> },
          { path: "patient/reviews", element: <PatientReviewsPage /> },
        ],
      },
      {
        element: <ProtectedRoute allowedRoles={["DOCTOR"]} />,
        children: [
          { path: "doctor/dashboard", element: <DoctorDashboardPage /> },
          { path: "doctor/appointments", element: <DoctorAppointmentsPage /> },
          { path: "doctor/availability", element: <DoctorAvailabilityPage /> },
          { path: "doctor/prescriptions", element: <DoctorPrescriptionsPage /> },
        ],
      },
      {
        element: <ProtectedRoute allowedRoles={["ADMIN"]} />,
        children: [
          { path: "admin/dashboard", element: <AdminDashboardPage /> },
          { path: "admin/invitations", element: <AdminInvitationsPage /> },
          { path: "admin/doctors", element: <AdminDoctorsPage /> },
          { path: "admin/appointments", element: <AdminAppointmentsPage /> },
          { path: "admin/reviews", element: <AdminReviewsPage /> },
          { path: "admin/overrides", element: <AdminOverridesPage /> },
        ],
      },
    ],
  },
]);
