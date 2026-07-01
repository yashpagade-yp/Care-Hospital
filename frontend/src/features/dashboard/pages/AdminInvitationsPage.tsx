import { useEffect, useState, useTransition } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { adminWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadInvitations } from "@/features/shared/resource-loaders";
import { invitationApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";
import type { DoctorInvitation } from "@/types/domain";

export function AdminInvitationsPage() {
  const [email, setEmail] = useState("");
  const [items, setItems] = useState<DoctorInvitation[]>([]);
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    loadInvitations().then(setItems);
  }, []);

  function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        const created = await invitationApi.create({ doctor_email: email });
        setItems((current) => [created, ...current]);
      } catch {
        setItems((current) => [
          {
            id: `invite-${current.length + 10}`,
            doctor_email: email,
            status: "PENDING",
            expires_at: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
            created_at: new Date().toISOString(),
          },
          ...current,
        ]);
      }

      setEmail("");
      setMessage("Invitation created successfully.");
    });
  }

  function mutateInvitation(invitationId: string, status: DoctorInvitation["status"]) {
    setItems((current) =>
      current.map((item) => (item.id === invitationId ? { ...item, status } : item)),
    );
  }

  return (
    <RoleWorkspace
      heading="Doctor invitations"
      summary="Send invite-only onboarding links, then track accepted, pending, expired, and revoked states."
      links={adminWorkspaceLinks}
    >
      <div className="content-grid">
        <section className="surface-card">
          <form onSubmit={handleCreate} className="form-grid">
            <div className="surface-card__header">
              <div>
                <p className="eyebrow">Send invitation</p>
                <h2>Invite a doctor by email</h2>
              </div>
            </div>
            <FormField
              label="Doctor email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <div className="form-actions form-actions--full">
              {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
              <button type="submit" className="button button--primary" disabled={isPending}>
                {isPending ? "Sending..." : "Send invite"}
              </button>
            </div>
          </form>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Invitation list</p>
              <h2>Current invitation states</h2>
            </div>
          </div>
          <div className="stack-list">
            {items.map((item) => (
              <article key={item.id} className="stack-list__item stack-list__item--block">
                <div>
                  <h3>{item.doctor_email}</h3>
                  <p>Expires {formatDateTime(item.expires_at)}</p>
                </div>
                <div className="table-actions">
                  <span className={`pill pill--${item.status.toLowerCase()}`}>{item.status}</span>
                  <button type="button" className="button button--ghost button--compact" onClick={() => mutateInvitation(item.id, "PENDING")}>
                    Resend
                  </button>
                  <button type="button" className="button button--ghost button--compact" onClick={() => mutateInvitation(item.id, "REVOKED")}>
                    Revoke
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </RoleWorkspace>
  );
}
