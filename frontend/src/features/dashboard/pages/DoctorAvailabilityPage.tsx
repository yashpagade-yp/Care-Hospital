import { useEffect, useState, useTransition } from "react";

import { SidebarLayout } from "@/components/layout/SidebarLayout";
import { DOCTOR_NAV } from "./DoctorDashboardPage";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useAppSession } from "@/features/auth/session/AppSessionProvider";
import { availabilityApi } from "@/lib/api/endpoints";
import type { AvailabilityType, DoctorAvailability } from "@/types/domain";

// Day names in order matching JS getDay() (0 = Sunday)
const JS_DAY_NAMES = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];

const DAY_OPTIONS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"];

const labelStyle: React.CSSProperties = {
  fontSize: "0.82rem", fontWeight: 600, color: "var(--text-soft)",
  display: "block", marginBottom: "0.3rem",
};
const inputStyle: React.CSSProperties = {
  width: "100%", padding: "0.6rem 0.85rem",
  border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
  fontSize: "0.9rem", fontFamily: "inherit", background: "var(--surface)",
  color: "var(--text)",
};

type Form = {
  availability_type: AvailabilityType;
  pick_date: string;          // date picker — auto derives day_of_week for RECURRING
  day_of_week: string;        // auto-filled from pick_date
  start_time: string;
  end_time: string;
  exception_date: string;     // only used when type != RECURRING
};

export function DoctorAvailabilityPage() {
  const { session } = useAppSession();
  const [items, setItems] = useState<DoctorAvailability[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isPending, startTransition] = useTransition();
  const [showConfirm, setShowConfirm] = useState(false);
  const [isClearing, setIsClearing] = useState(false);

  const [form, setForm] = useState<Form>({
    availability_type: "RECURRING",
    pick_date: "",
    day_of_week: "",
    start_time: "09:00",
    end_time: "13:00",
    exception_date: "",
  });

  // Load availability from backend on mount (persists across refresh)
  useEffect(() => {
    if (!session) return;
    setLoading(true);
    availabilityApi.listDoctorAvailability(session.user.id)
      .then((res) => setItems(res.items ?? []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [session]);

  // Auto-derive day_of_week from the picked date
  function handleDatePick(dateStr: string) {
    let dayName = "";
    if (dateStr) {
      const d = new Date(dateStr + "T00:00:00"); // force local midnight
      dayName = JS_DAY_NAMES[d.getDay()];
    }
    setForm((f) => ({
      ...f,
      pick_date: dateStr,
      day_of_week: dayName,
      // For EXCEPTION type, use the same picked date as exception_date
      exception_date: form.availability_type !== "RECURRING" ? dateStr : f.exception_date,
    }));
  }

  function handleTypeChange(type: AvailabilityType) {
    setForm((f) => ({
      ...f,
      availability_type: type,
      // If switching to RECURRING, clear exception_date; else populate from pick_date
      exception_date: type !== "RECURRING" ? f.pick_date : "",
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    setError("");

    const payload: { availability_type: string; start_time: string; end_time: string; day_of_week?: string; exception_date?: string } = {
      availability_type: form.availability_type,
      start_time: form.start_time,
      end_time: form.end_time,
    };
    if (form.availability_type === "RECURRING") {
      if (!form.day_of_week) { setError("Please pick a date to auto-fill the day."); return; }
      payload.day_of_week = form.day_of_week;
    } else {
      if (!form.exception_date) { setError("Please pick a date for this exception."); return; }
      payload.exception_date = form.exception_date;
    }

    startTransition(async () => {
      try {
        const created = await availabilityApi.createDoctorAvailability(payload);
        setItems((cur) => [created, ...cur]);
        setMessage("Availability saved successfully.");
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to save availability.";
        setError(msg);
      }
    });
  }

  // "Update Availability" — delete all and start fresh
  async function handleClearAll() {
    if (!session) return;
    setIsClearing(true);
    setShowConfirm(false);
    try {
      await Promise.all(items.map((item) => availabilityApi.deleteAvailability(item.id)));
      setItems([]);
      setMessage("All availability slots cleared. You can now create new ones.");
    } catch {
      setError("Failed to clear some slots. Please try again.");
    } finally {
      setIsClearing(false);
    }
  }

  return (
    <SidebarLayout sections={DOCTOR_NAV}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", padding: "1.5rem" }}>

        {/* ── Left: Create form ── */}
        <div className="ws-card">
          <div className="ws-card__header">
            <p className="ws-card__eyebrow">Create availability</p>
            <h2 className="ws-card__title">Working slot form</h2>
          </div>
          <form onSubmit={handleSubmit} style={{ padding: "0 1.25rem 1.25rem", display: "flex", flexDirection: "column", gap: "0.85rem" }}>

            {/* Availability type */}
            <div>
              <label style={labelStyle}>Availability type</label>
              <select
                value={form.availability_type}
                onChange={(e) => handleTypeChange(e.target.value as AvailabilityType)}
                style={inputStyle}
              >
                <option value="RECURRING">RECURRING (weekly)</option>
                <option value="EXCEPTION_AVAILABLE">EXCEPTION – Available</option>
                <option value="EXCEPTION_BLOCKED">EXCEPTION – Blocked</option>
              </select>
            </div>

            {/* Date picker → auto day */}
            <div>
              <label style={labelStyle}>
                {form.availability_type === "RECURRING"
                  ? "Pick any date — day of week auto-fills ↓"
                  : "Exception date"}
              </label>
              <input
                type="date"
                value={form.pick_date}
                onChange={(e) => handleDatePick(e.target.value)}
                required
                style={inputStyle}
              />
            </div>

            {/* Auto-filled day badge (RECURRING only) */}
            {form.availability_type === "RECURRING" && (
              <div>
                <label style={labelStyle}>Day of week (auto-detected)</label>
                <div style={{
                  padding: "0.6rem 0.85rem",
                  border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                  background: form.day_of_week ? "#f0fdf4" : "#f8f9fa",
                  color: form.day_of_week ? "#166534" : "var(--text-soft)",
                  fontWeight: form.day_of_week ? 700 : 400,
                  fontSize: "0.9rem",
                }}>
                  {form.day_of_week || "— pick a date above —"}
                </div>
              </div>
            )}

            {/* Start / End time */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
              <div>
                <label style={labelStyle}>Start time</label>
                <input
                  type="time"
                  value={form.start_time}
                  onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
                  required
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>End time</label>
                <input
                  type="time"
                  value={form.end_time}
                  onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
                  required
                  style={inputStyle}
                />
              </div>
            </div>

            {message && <StatusBanner tone="success">{message}</StatusBanner>}
            {error && <StatusBanner tone="error">{error}</StatusBanner>}

            <button
              type="submit"
              className="ws-btn ws-btn--primary ws-btn--full"
              disabled={isPending}
            >
              {isPending ? "Saving…" : "Save availability"}
            </button>
          </form>
        </div>

        {/* ── Right: List ── */}
        <div className="ws-card" style={{ height: "fit-content" }}>
          <div className="ws-card__header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <p className="ws-card__eyebrow">Availability list</p>
              <h2 className="ws-card__title">Current slots</h2>
            </div>
            {items.length > 0 && (
              <button
                onClick={() => setShowConfirm(true)}
                disabled={isClearing}
                style={{
                  padding: "0.45rem 0.9rem", fontSize: "0.82rem", fontWeight: 600,
                  borderRadius: "var(--radius-sm)", border: "1px solid #ef4444",
                  background: "transparent", color: "#ef4444", cursor: "pointer",
                  whiteSpace: "nowrap",
                }}
              >
                {isClearing ? "Clearing…" : "⟳ Update Availability"}
              </button>
            )}
          </div>

          {/* Confirmation dialog */}
          {showConfirm && (
            <div style={{
              margin: "0 1.25rem 1rem",
              padding: "1rem", borderRadius: "var(--radius-sm)",
              background: "#fef2f2", border: "1px solid #fca5a5",
            }}>
              <p style={{ fontWeight: 600, color: "#991b1b", marginBottom: "0.5rem" }}>
                Are you sure you want to clear all availability slots?
              </p>
              <p style={{ fontSize: "0.82rem", color: "#7f1d1d", marginBottom: "0.85rem" }}>
                This will remove all current slots. You can then create new ones.
              </p>
              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  onClick={handleClearAll}
                  style={{
                    padding: "0.45rem 1rem", background: "#ef4444", color: "#fff",
                    border: "none", borderRadius: "var(--radius-sm)", cursor: "pointer", fontWeight: 600,
                  }}
                >
                  Yes, clear all
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  style={{
                    padding: "0.45rem 1rem", background: "transparent",
                    border: "1px solid var(--line)", borderRadius: "var(--radius-sm)", cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div style={{ padding: "0 1.25rem 1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {loading ? (
              <p style={{ color: "var(--text-soft)", fontSize: "0.88rem" }}>Loading…</p>
            ) : items.length === 0 ? (
              <p style={{ color: "var(--text-soft)", fontSize: "0.88rem" }}>No availability slots yet.</p>
            ) : (
              items.map((item) => (
                <div key={item.id} style={{
                  padding: "0.85rem 1rem",
                  border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                  background: "var(--surface)",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <span style={{
                        fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.05em",
                        color: item.availability_type === "RECURRING" ? "#1d4ed8" : "#9a3412",
                        background: item.availability_type === "RECURRING" ? "#dbeafe" : "#ffedd5",
                        padding: "0.2rem 0.55rem", borderRadius: "999px",
                      }}>
                        {item.availability_type}
                      </span>
                      <p style={{ marginTop: "0.45rem", fontWeight: 600, fontSize: "0.9rem" }}>
                        {item.day_of_week ?? item.exception_date ?? "Custom"}
                      </p>
                      <p style={{ fontSize: "0.88rem", color: "var(--text-soft)" }}>
                        {item.start_time?.slice(0, 5)} – {item.end_time?.slice(0, 5)}
                      </p>
                    </div>
                    <button
                      onClick={async () => {
                        try {
                          await availabilityApi.deleteAvailability(item.id);
                          setItems((cur) => cur.filter((i) => i.id !== item.id));
                        } catch {
                          setError("Failed to delete slot.");
                        }
                      }}
                      title="Delete this slot"
                      style={{
                        background: "transparent", border: "none", cursor: "pointer",
                        color: "#ef4444", fontSize: "1.1rem", lineHeight: 1,
                        padding: "0.2rem 0.4rem",
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
