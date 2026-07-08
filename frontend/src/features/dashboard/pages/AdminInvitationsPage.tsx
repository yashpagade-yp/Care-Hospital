import { useEffect, useState, useTransition } from "react";
import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { invitationApi } from "@/lib/api/endpoints";
import type { DoctorInvitation } from "@/types/domain";
import { ADMIN_NAV } from "./AdminDashboardPage";

export function AdminInvitationsPage() {
  const [email, setEmail] = useState("");
  const [items, setItems] = useState<DoctorInvitation[]>([]);
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    invitationApi.list().then((res) => setItems(res.invitations)).catch(() => {});
  }, []);

  function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        const created = await invitationApi.create({ doctor_email: email });
        setItems((current) => [created, ...current]);
        setMessage(`Invitation sent to ${email}.`);
      } catch {
        setMessage("Could not send the invitation. Please try again.");
      }
      setEmail("");
    });
  }

  async function handleResend(id: string) {
    try {
      await invitationApi.resend({ invitation_id: id });
      setItems((current) =>
        current.map((item) => (item.id === id ? { ...item, status: "PENDING" } : item)),
      );
    } catch {}
  }

  async function handleRevoke(id: string) {
    try {
      await invitationApi.revoke({ invitation_id: id });
      setItems((current) =>
        current.map((item) => (item.id === id ? { ...item, status: "REVOKED" } : item)),
      );
    } catch {}
  }

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      <div className="ws-page-header">
        <p className="ws-page-eyebrow">Admin Workspace</p>
        <h1 className="ws-page-heading">Doctor Invitations</h1>
        <p className="ws-page-sub">
          Send invite-only onboarding links and track accepted, pending, expired, and revoked states.
        </p>
      </div>

      <div className="ws-grid ws-grid--2">
        {/* Invite form */}
        <div className="ws-card">
          <div className="ws-card__header">
            <h2 className="ws-card__title">Send an invitation</h2>
          </div>
          <form className="ws-invite-form" onSubmit={handleCreate}>
            <input
              type="email"
              placeholder="doctor@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              id="inv-email-input"
            />
            {message && (
              <p style={{ fontSize: "0.85rem", color: "var(--green)", margin: 0 }}>{message}</p>
            )}
            <button
              type="submit"
              className="ws-btn ws-btn--primary ws-btn--full"
              disabled={isPending}
            >
              {isPending ? "Sending…" : "Send invitation"}
            </button>
          </form>
        </div>

        {/* Invitation stats */}
        <div className="ws-card">
          <div className="ws-card__header">
            <h2 className="ws-card__title">Summary</h2>
          </div>
          <div className="ws-glance-grid">
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Total sent</span>
              <span className="ws-glance-tile__value">{items.length}</span>
            </div>
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Pending</span>
              <span className="ws-glance-tile__value">
                {items.filter((i) => i.status === "PENDING").length}
              </span>
            </div>
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Accepted</span>
              <span className="ws-glance-tile__value">
                {items.filter((i) => i.status === "ACCEPTED").length}
              </span>
            </div>
            <div className="ws-glance-tile">
              <span className="ws-glance-tile__label">Expired / Revoked</span>
              <span className="ws-glance-tile__value">
                {items.filter((i) => i.status === "EXPIRED" || i.status === "REVOKED").length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Invitation list */}
      <div className="ws-card" style={{ marginTop: "1.25rem" }}>
        <div className="ws-card__header">
          <h2 className="ws-card__title">All invitations</h2>
        </div>
        {items.length === 0 ? (
          <div className="ws-empty">
            <div className="ws-empty__icon">📧</div>
            <p className="ws-empty__title">No invitations yet</p>
            <p className="ws-empty__sub">Send your first doctor invitation above.</p>
          </div>
        ) : (
          <div className="ws-table-wrap">
            <table className="ws-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Expires</th>
                  <th>Sent on</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }}>{item.doctor_email}</td>
                    <td>
                      <span className={`ws-badge ws-badge--${item.status.toLowerCase()}`}>
                        {item.status}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.85rem" }}>
                      {new Date(item.expires_at).toLocaleDateString()}
                    </td>
                    <td style={{ color: "var(--text-soft)", fontSize: "0.85rem" }}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="ws-action-row">
                        {item.status === "PENDING" && (
                          <button
                            type="button"
                            className="ws-btn ws-btn--ghost"
                            onClick={() => handleResend(item.id)}
                          >
                            Resend
                          </button>
                        )}
                        {item.status !== "REVOKED" && item.status !== "ACCEPTED" && (
                          <button
                            type="button"
                            className="ws-btn ws-btn--danger"
                            onClick={() => handleRevoke(item.id)}
                          >
                            Revoke
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </SidebarLayout>
  );
}
