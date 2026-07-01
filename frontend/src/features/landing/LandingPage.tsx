import { Link } from "react-router-dom";

import { ButtonLink } from "@/components/ui/ButtonLink";
import { RouteCard } from "@/components/ui/RouteCard";
import {
  adminBenefits,
  doctorBenefits,
  featuredAreas,
  landingSlides,
  patientBenefits,
} from "@/features/landing/content";

export function LandingPage() {
  return (
    <div className="landing-page">
      <HeroCarousel />
      <TrustBand />
      <CareModelSection />
      <PlatformFlowSection />
      <FeatureAreasSection />
      <AccessSection />
    </div>
  );
}

function HeroCarousel() {
  return (
    <section className="hero-carousel">
      <div className="hero-carousel__track">
        {landingSlides.map((slide) => (
          <article
            key={slide.title}
            className={`hero-slide hero-slide--${slide.accent}`}
          >
            <div className="shell hero-slide__content">
              <div className="hero-slide__copy">
                <p className="eyebrow">MedCare hospital platform</p>
                <h1>{slide.title}</h1>
                <p>{slide.body}</p>
                <div className="hero-slide__actions">
                  <ButtonLink to="/patient/book">{slide.ctaPrimary}</ButtonLink>
                  <ButtonLink to="/login" variant="secondary">
                    {slide.ctaSecondary}
                  </ButtonLink>
                </div>
              </div>
              <div className="hero-slide__visual" aria-hidden="true">
                <div className="hero-slide__orb hero-slide__orb--large" />
                <div className="hero-slide__orb hero-slide__orb--small" />
                <div className="hero-slide__panel">
                  <span>Patients</span>
                  <span>Doctors</span>
                  <span>Admins</span>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>

      <div className="hero-carousel__dots" aria-hidden="true">
        {landingSlides.map((slide) => (
          <span key={slide.title} className="hero-carousel__dot" />
        ))}
      </div>
    </section>
  );
}

function TrustBand() {
  return (
    <section className="trust-band shell">
      <div>
        <p className="eyebrow">Designed from your project flow</p>
        <h2>Built around the exact patient, doctor, and admin journeys in your docs.</h2>
      </div>
      <div className="trust-band__stats">
        <div>
          <strong>1</strong>
          <span>shared login flow</span>
        </div>
        <div>
          <strong>3</strong>
          <span>role-specific workspaces</span>
        </div>
        <div>
          <strong>6</strong>
          <span>landing panels</span>
        </div>
      </div>
    </section>
  );
}

function CareModelSection() {
  return (
    <section className="split-section shell">
      <div className="split-section__copy">
        <p className="eyebrow">Patient-first landing</p>
        <h2>Healing starts with clarity, not clutter.</h2>
        <p>
          The landing page keeps the premium hospital tone from your references, but uses
          less imagery and more clear content blocks so patients can understand what MedCare
          does quickly.
        </p>
        <ul className="bullet-list">
          {patientBenefits.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="split-section__visual split-section__visual--soft">
        <div className="info-panel">
          <p className="eyebrow">Care access</p>
          <h3>From landing page to confirmed appointment in a focused three-step flow.</h3>
          <div className="info-panel__mini-grid">
            <span>Choose doctor</span>
            <span>Hold slot</span>
            <span>Confirm details</span>
            <span>Mock payment</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function PlatformFlowSection() {
  return (
    <section className="platform-flow">
      <div className="shell">
        <div className="section-heading">
          <p className="eyebrow">Platform architecture</p>
          <h2>Frontend routes reflect the actual operational flow.</h2>
          <p>
            Instead of a generic website shell, the app structure is already prepared for
            registration, OTP, doctor invitation validation, onboarding, dashboards, and
            booking.
          </p>
        </div>

        <div className="route-grid">
          <RouteCard
            title="Patient access"
            description="Registration, OTP verification, booking, dashboard, prescriptions, and reviews."
            icon="P"
          />
          <RouteCard
            title="Doctor access"
            description="Invite validation, credentials, OTP, profile completion, schedule, and appointment follow-up."
            icon="D"
          />
          <RouteCard
            title="Admin access"
            description="Doctor invitations, operational appointment oversight, and role-safe hospital management."
            icon="A"
          />
        </div>
      </div>
    </section>
  );
}

function FeatureAreasSection() {
  return (
    <section className="feature-areas shell">
      <div className="feature-areas__intro">
        <p className="eyebrow">Featured care areas</p>
        <h2>Clinical departments can be surfaced without copying the reference site.</h2>
        <p>
          This section uses the same clean list-driven confidence from the reference design,
          but keeps the content specific to MedCare’s own positioning.
        </p>
      </div>

      <div className="feature-areas__list">
        {featuredAreas.map((area) => (
          <Link key={area} to="/patient/book" className="feature-link">
            <span>{area}</span>
            <span aria-hidden="true">›</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

function AccessSection() {
  return (
    <section className="access-section">
      <div className="shell access-section__grid">
        <div className="access-column">
          <p className="eyebrow">Doctor workspace</p>
          <h3>Controlled onboarding and protected clinical actions.</h3>
          <ul className="bullet-list">
            {doctorBenefits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="access-column">
          <p className="eyebrow">Admin workspace</p>
          <h3>Operational visibility without crossing into clinical access.</h3>
          <ul className="bullet-list">
            {adminBenefits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
