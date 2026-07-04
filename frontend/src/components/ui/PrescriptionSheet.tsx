type PrescriptionSheetProps = {
  hospitalName: string;
  hospitalAddress: string;
  doctorName: string;
  patientName: string;
  issuedAt: string;
  medicines: string[];
  visitReason?: string | null;
  patientPhone?: string | null;
  patientAge?: number | null;
  patientGender?: string | null;
  patientBloodGroup?: string | null;
  notes?: string | null;
};

export function PrescriptionSheet({
  hospitalName,
  hospitalAddress,
  doctorName,
  patientName,
  issuedAt,
  medicines,
  visitReason,
  patientPhone,
  patientAge,
  patientGender,
  patientBloodGroup,
  notes,
}: PrescriptionSheetProps) {
  const patientMeta = [
    patientAge ? `${patientAge} years` : null,
    patientGender ?? null,
    patientBloodGroup ? `Blood Group ${patientBloodGroup}` : null,
  ].filter(Boolean);

  return (
    <article className="prescription-sheet">
      <header className="prescription-sheet__header">
        <div>
          <p className="prescription-sheet__eyebrow">Hospital Prescription</p>
          <h3 className="prescription-sheet__hospital">{hospitalName}</h3>
          <p className="prescription-sheet__address">{hospitalAddress}</p>
        </div>
        <div className="prescription-sheet__stamp">
          <span className="prescription-sheet__stamp-label">Issued on</span>
          <strong>{issuedAt}</strong>
        </div>
      </header>

      <section className="prescription-sheet__patient">
        <div className="prescription-sheet__patient-row">
          <span>Patient</span>
          <strong>{patientName}</strong>
        </div>
        <div className="prescription-sheet__patient-row">
          <span>Treating doctor</span>
          <strong>{doctorName}</strong>
        </div>
        <div className="prescription-sheet__patient-row">
          <span>Patient details</span>
          <strong>{patientMeta.length ? patientMeta.join(" • ") : "Not provided"}</strong>
        </div>
        <div className="prescription-sheet__patient-row">
          <span>Phone</span>
          <strong>{patientPhone ?? "Not provided"}</strong>
        </div>
        <div className="prescription-sheet__patient-row prescription-sheet__patient-row--wide">
          <span>Visit reason</span>
          <strong>{visitReason ?? "Not provided"}</strong>
        </div>
      </section>

      <section className="prescription-sheet__body">
        <div className="prescription-sheet__rx">Rx</div>
        <ol className="prescription-sheet__medicines">
          {medicines.map((medicine) => (
            <li key={medicine}>{medicine}</li>
          ))}
        </ol>
      </section>

      <footer className="prescription-sheet__footer">
        <div>
          <span className="prescription-sheet__footer-label">Additional notes</span>
          <p>{notes ?? "No additional notes."}</p>
        </div>
        <div className="prescription-sheet__signature">
          <span className="prescription-sheet__footer-label">Consulting doctor</span>
          <strong>{doctorName}</strong>
        </div>
      </footer>
    </article>
  );
}
