import { useEffect, useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { ADMIN_NAV } from "./AdminDashboardPage";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { doctorDirectory } from "@/lib/mock/data";
import { loadDoctorReviews } from "@/features/shared/resource-loaders";
import { reviewApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";
import type { Review } from "@/types/domain";

export function AdminReviewsPage() {
  const [doctorId, setDoctorId] = useState(doctorDirectory[0]?.id ?? "");
  const [items, setItems] = useState<Review[]>([]);
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    loadDoctorReviews(doctorId, true).then(setItems);
  }, [doctorId]);

  function toggleVisibility(reviewId: string, isHidden: boolean) {
    setMessage("");
    startTransition(async () => {
      try {
        const updated = await reviewApi.setReviewVisibility(reviewId, { is_hidden: isHidden });
        setItems((current) => current.map((item) => (item.id === reviewId ? updated : item)));
      } catch {
        setItems((current) =>
          current.map((item) => (item.id === reviewId ? { ...item, is_hidden: isHidden } : item)),
        );
      }
      setMessage("Review visibility updated.");
    });
  }

  return (
    <SidebarLayout sections={ADMIN_NAV}>
      <section className="surface-card">
        <div className="surface-card__header">
          <div>
            <p className="eyebrow">Doctor review selection</p>
            <h2>Moderation queue</h2>
          </div>
        </div>
        <FormField
          label="Doctor ID"
          value={doctorId}
          onChange={(event) => setDoctorId(event.target.value)}
        />
        {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
        <div className="stack-list">
          {items.map((review) => (
            <article key={review.id} className="stack-list__item stack-list__item--block">
              <div>
                <h3>{review.rating}/5 rating</h3>
                <p>{formatDateTime(review.created_at)}</p>
              </div>
              <p>{review.comment ?? "No comment."}</p>
              <button
                type="button"
                className="button button--ghost button--compact"
                onClick={() => toggleVisibility(review.id, !review.is_hidden)}
                disabled={isPending}
              >
                {review.is_hidden ? "Make visible" : "Hide review"}
              </button>
            </article>
          ))}
        </div>
      </section>
    </SidebarLayout>
  );
}
