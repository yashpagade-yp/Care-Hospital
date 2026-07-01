import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { adminWorkspaceLinks } from "@/features/shared/workspace-links";
import { loadAdminDashboard } from "@/features/shared/resource-loaders";
import { useAsyncResource } from "@/hooks/useAsyncResource";
import { formatDateTime } from "@/lib/utils/format";

export function AdminDashboardPage() {
  const { data, isLoading, error } = useAsyncResource(loadAdminDashboard, []);

  return (
    <RoleWorkspace
      heading="Admin dashboard"
      summary="Monitor invitations, doctor activity, appointment volume, and moderation queues from an operational workspace."
      links={adminWorkspaceLinks}
    >
      {error ? <StatusBanner tone="warning">{error}</StatusBanner> : null}
      {isLoading || !data ? (
        <div className="loading-panel">Loading admin workspace...</div>
      ) : (
        <>
          <div className="stats-grid">
            <StatCard label="Doctors" value={data.doctor_count} />
            <StatCard label="Invitations" value={data.invitation_count} />
            <StatCard label="Appointments" value={data.appointment_count} />
            <StatCard label="Flagged reviews" value={data.flagged_reviews.length} />
          </div>
          <div className="content-grid">
            <section className="surface-card">
              <div className="surface-card__header">
                <div>
                  <p className="eyebrow">Recent invitations</p>
                  <h2>Invitation workflow</h2>
                </div>
              </div>
              <div className="stack-list">
                {data.recent_invitations.map((invitation) => (
                  <article key={invitation.id} className="stack-list__item">
                    <div>
                      <h3>{invitation.doctor_email}</h3>
                      <p>Expires {formatDateTime(invitation.expires_at)}</p>
                    </div>
                    <strong>{invitation.status}</strong>
                  </article>
                ))}
              </div>
            </section>
            <section className="surface-card">
              <div className="surface-card__header">
                <div>
                  <p className="eyebrow">Moderation queue</p>
                  <h2>Flagged reviews</h2>
                </div>
              </div>
              <div className="stack-list">
                {data.flagged_reviews.map((review) => (
                  <article key={review.id} className="stack-list__item stack-list__item--block">
                    <div>
                      <h3>{review.doctor_id}</h3>
                      <p>{formatDateTime(review.created_at)}</p>
                    </div>
                    <p>{review.comment ?? "No comment."}</p>
                  </article>
                ))}
              </div>
            </section>
          </div>
        </>
      )}
    </RoleWorkspace>
  );
}
