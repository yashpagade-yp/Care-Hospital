import { useEffect, useTransition, useState } from "react";
import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { dashboardApi, invitationApi } from "@/lib/api/endpoints";
import type { AdminDashboard } from "@/types/domain";

const ADMIN_NAV = [
  {
    title: "Platform",
    links: [
      { label: "Dashboard", to: "/admin/dashboard" },
      { label: "Invitations", to: "/admin/invitations" },
    ],
  },
  {
    title: "Workspace",
    links: [
      { label: "Doctors & Patients", to: "/admin/doctors" },
      { label: "All Appointments", to: "/admin/appointments" },
      { label: "Availability Overrides", to: "/admin/overrides" },
      { label: "Review Moderation", to: "/admin/reviews" },
    ],
  },
];

export function AdminDashboardPage() {
  const { session } = useAppSession();
  const [isPending, startTransition] = useTransition();
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteStatus, setInviteStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [inviteMessage, setInviteMessage] = useState("");

  useEffect(() => {
    startTransition(async () => {
      try {
        const result = await dashboardApi.admin();
        setData(result);
      } catch {
        // Demo mode: data stays null
      }
    });
  }, []);

  async function handleInvite(event: React.FormEvent) {
    event.preventDefault();
    if (!inviteEmail.trim()) return;
    setInviteStatus("sending");
    setInviteMessage("");
    try {
      await invitationApi.create({ doctor_email: inviteEmail });
      setInviteStatus("sent");
      setInviteMessage(`An invitation has been sent to ${inviteEmail}.`);
      setInviteEmail("");
    } catch {
      setInviteStatus("error");
      setInviteMessage("Could not send the invitation. Please try again.");
    }
  }

  const adminName = session?.user.name ?? "Admin";

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      {/* ── Page header ── */}
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Admin Workspace</p>
        <h1 className="ws-page-heading">Good day, {adminName.split(" ")[0]} 👋</h1>
        <p className="ws-page-sub">
          Here's a snapshot of your hospital platform — doctors, patients, and appointments at a glance.
        </p>
      </div>

      {/* ── Stat cards ── */}
      <div className="ws-stats-row">
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.doctor_count ?? "—"}</span>
          <span className="ws-stat-card__label">Active doctors</span>
          <span className="ws-stat-card__accent">on the platform</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.invitation_count ?? "—"}</span>
          <span className="ws-stat-card__label">Invitations sent</span>
          <span className="ws-stat-card__accent">total invites issued</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.appointment_count ?? "—"}</span>
          <span className="ws-stat-card__label">Total appointments</span>
          <span className="ws-stat-card__accent">across all doctors</span>
        </div>
        <div className="ws-stat-card">
          <span className="ws-stat-card__value">{data?.flagged_reviews?.length ?? "—"}</span>
          <span className="ws-stat-card__label">Reviews to review</span>
          <span className="ws-stat-card__accent">flagged for attention</span>
        </div>
      </div>

      {/* ── Two-panel content ── */}
      <div className="ws-grid ws-grid--2">
        {/* Invite a doctor */}
        <div className="ws-card">
          <div className="ws-card__header">
            <div>
              <h2 className="ws-card__title">Invite a doctor</h2>
              <p className="ws-card__sub">
                Enter the doctor's email — they'll receive an invitation to join MedCare.
              </p>
            </div>
          </div>
          <form className="ws-invite-form" onSubmit={handleInvite}>
            <input
              type="email"
              placeholder="doctor@example.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
              id="invite-email-input"
            />
            {inviteMessage && (
              <p
                style={{
                  fontSize: "0.85rem",
                  color: inviteStatus === "sent" ? "var(--green)" : "var(--status-danger-text)",
                  margin: 0,
                }}
              >
                {inviteMessage}
              </p>
            )}
            <button
              type="submit"
              className="ws-btn ws-btn--primary ws-btn--full"
              disabled={inviteStatus === "sending"}
            >
              {inviteStatus === "sending" ? "Sending…" : "Send invitation"}
            </button>
          </form>
        </div>

        {/* Workspace at a glance */}
        <div className="ws-card">
          <div className="ws-card__header">
            <div>
              <h2 className="ws-card__title">Workspace at a glance</h2>
              <p className="ws-card__sub">Recent platform activity summary.</p>
            </div>
          </div>
          <div className="ws-glance-grid">
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Recent invitations</span>
              <span className="ws-glance-tile__value">
                {data?.recent_invitations?.length ?? "—"}
              </span>
              <span className="ws-glance-tile__detail">latest batch</span>
            </div>
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Pending invites</span>
              <span className="ws-glance-tile__value">
                {data?.recent_invitations?.filter((i) => i.status === "PENDING").length ?? "—"}
              </span>
              <span className="ws-glance-tile__detail">waiting to accept</span>
            </div>
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Recent appointments</span>
              <span className="ws-glance-tile__value">
                {data?.recent_appointments?.length ?? "—"}
              </span>
              <span className="ws-glance-tile__detail">last scheduled</span>
            </div>
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Flagged reviews</span>
              <span className="ws-glance-tile__value">
                {data?.flagged_reviews?.length ?? "—"}
              </span>
              <span className="ws-glance-tile__detail">need moderation</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Recent invitations list ── */}
      {data?.recent_invitations && data.recent_invitations.length > 0 && (
        <div className="ws-card" style={{ marginTop: "1.25rem" }}>
          <div className="ws-card__header">
            <h2 className="ws-card__title">Recent invitations</h2>
          </div>
          <div className="ws-list">
            {data.recent_invitations.slice(0, 5).map((inv) => (
              <div key={inv.id} className="ws-list-item">
                <div className="ws-list-item__main">
                  <span className="ws-list-item__title">{inv.doctor_email}</span>
                  <span className="ws-list-item__sub">
                    Sent {new Date(inv.created_at).toLocaleDateString()} · Expires{" "}
                    {new Date(inv.expires_at).toLocaleDateString()}
                  </span>
                </div>
                <span
                  className={`ws-badge ws-badge--${inv.status.toLowerCase()}`}
                >
                  {inv.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {isPending && <div className="ws-loading">Loading dashboard data…</div>}
    </SidebarLayout>
  );
}

export { ADMIN_NAV };
