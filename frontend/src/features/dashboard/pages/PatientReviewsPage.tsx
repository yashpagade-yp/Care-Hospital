import { useMemo, useState, useTransition } from "react";

import { RoleWorkspace } from "@/components/layout/RoleWorkspace";
import { FormField } from "@/components/ui/FormField";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { patientWorkspaceLinks } from "@/features/shared/workspace-links";
import { doctorCards, reviews as mockReviews } from "@/lib/mock/data";
import { reviewApi } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils/format";

export function PatientReviewsPage() {
  const { session } = useAppSession();
  const [isPending, startTransition] = useTransition();
  const [appointmentId, setAppointmentId] = useState("appt-002");
  const [rating, setRating] = useState("5");
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [items, setItems] = useState(mockReviews.filter((item) => !item.is_hidden));

  const visibleReviews = useMemo(() => items.filter((item) => !item.is_hidden), [items]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");

    startTransition(async () => {
      try {
        const created = await reviewApi.createReview({
          appointment_id: appointmentId,
          rating: Number(rating),
          comment,
        });
        setItems((current) => [created, ...current]);
      } catch {
        setItems((current) => [
          {
            id: `review-${current.length + 10}`,
            appointment_id: appointmentId,
            patient_id: session?.user.id ?? "patient-demo",
            doctor_id: "doctor-202",
            rating: Number(rating),
            comment,
            is_hidden: false,
            created_at: new Date().toISOString(),
          },
          ...current,
        ]);
      }

      setComment("");
      setMessage("Review saved successfully.");
    });
  }

  return (
    <RoleWorkspace
      heading="Patient reviews"
      summary="Leave one review after a completed appointment and browse visible doctor feedback."
      links={patientWorkspaceLinks}
    >
      <div className="content-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Submit a review</p>
              <h2>Post-consultation feedback</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={handleSubmit}>
            <FormField
              label="Appointment ID"
              value={appointmentId}
              onChange={(event) => setAppointmentId(event.target.value)}
            />
            <FormField
              label="Rating"
              type="number"
              min="1"
              max="5"
              value={rating}
              onChange={(event) => setRating(event.target.value)}
            />
            <div className="form-actions--full">
              <FormField
                as="textarea"
                label="Comment"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                rows={4}
              />
            </div>
            <div className="form-actions form-actions--full">
              {message ? <StatusBanner tone="success">{message}</StatusBanner> : null}
              <button type="submit" className="button button--primary" disabled={isPending}>
                {isPending ? "Submitting..." : "Submit review"}
              </button>
            </div>
          </form>
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="eyebrow">Visible reviews</p>
              <h2>Doctor feedback</h2>
            </div>
          </div>
          <div className="stack-list">
            {visibleReviews.map((review) => {
              const doctor = doctorCards.find((item) => item.doctor_id === review.doctor_id);
              return (
                <article key={review.id} className="stack-list__item stack-list__item--block">
                  <div>
                    <h3>{doctor?.name ?? review.doctor_id}</h3>
                    <p>{formatDateTime(review.created_at)}</p>
                  </div>
                  <strong>{review.rating}/5</strong>
                  <p>{review.comment ?? "No written comment."}</p>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </RoleWorkspace>
  );
}
