import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import consultationPhoto from "../../../reference/Doctor Patient Photo.jpg";
import { ButtonLink } from "@/components/ui/ButtonLink";
import {
  accessCards,
  doctorProfiles,
  helplines,
  hospitalStats,
  landingSlides,
  patientReviews,
  wellnessNotes,
} from "@/features/landing/content";

export function LandingPage() {
  return (
    <div className="hospital-landing">
      <HeroCarousel />
      <AccessSection />
      <HospitalStorySection />
      <DoctorsSection />
    </div>
  );
}

function HeroCarousel() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const timerId = window.setInterval(() => {
      setActiveIndex((currentIndex) => (currentIndex + 1) % landingSlides.length);
    }, 5000);

    return () => {
      window.clearInterval(timerId);
    };
  }, []);

  const activeSlide = landingSlides[activeIndex];

  return (
    <section className={`hospital-hero hospital-hero--${activeSlide.accent}`}>
      <div className="hospital-hero__veil" />
      <div className="shell hospital-hero__shell">
        <div className="hospital-hero__copy">
          <p className="eyebrow">{activeSlide.eyebrow}</p>
          <h1>{activeSlide.title}</h1>
          <p>{activeSlide.body}</p>

          <div className="hospital-hero__actions">
            <ButtonLink to="/login">Login</ButtonLink>
            <Link to="/patient/register" className="button button--secondary">
              Registration
            </Link>
          </div>

          <div className="hospital-hero__quote">
            <span className="hospital-hero__quote-mark">"</span>
            <p>{activeSlide.quote}</p>
          </div>
        </div>

        <div className="hospital-hero__visual">
          <div className="hospital-hero__image-card">
            <img src={consultationPhoto} alt="Doctor consulting with a patient" />
          </div>

          <div className="hospital-hero__stat-card">
            <span>{activeSlide.statLabel}</span>
            <strong>{activeSlide.statValue}</strong>
            <small>Trusted care, clear support, and a patient-first experience.</small>
          </div>

          <div className="hospital-hero__badge-row" aria-label="Hospital highlights">
            <span>24/7 ambulance</span>
            <span>Advanced ICU</span>
            <span>Warm specialists</span>
          </div>
        </div>
      </div>

      <div className="shell hospital-hero__controls">
        <div className="hospital-hero__arrow-group">
          <button
            type="button"
            className="hospital-hero__arrow"
            onClick={() =>
              setActiveIndex((currentIndex) =>
                currentIndex === 0 ? landingSlides.length - 1 : currentIndex - 1,
              )
            }
            aria-label="Previous slide"
          >
            Prev
          </button>
          <button
            type="button"
            className="hospital-hero__arrow"
            onClick={() =>
              setActiveIndex((currentIndex) => (currentIndex + 1) % landingSlides.length)
            }
            aria-label="Next slide"
          >
            Next
          </button>
        </div>

        <div className="hospital-hero__dots" aria-label="Slide navigation">
          {landingSlides.map((slide, index) => (
            <button
              key={slide.title}
              type="button"
              className={`hospital-hero__dot${index === activeIndex ? " hospital-hero__dot--active" : ""}`}
              onClick={() => setActiveIndex(index)}
              aria-label={`Show slide ${index + 1}`}
              aria-pressed={index === activeIndex}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function AccessSection() {
  return (
    <section className="hospital-access shell">
      <div className="section-heading hospital-access__heading">
        <p className="eyebrow">Simple patient access</p>
        <h2>Two clear paths. Login if you already have an account, or register if you are new.</h2>
        <p>
          The homepage keeps the decision simple so visitors can move forward quickly
          without scrolling through technical platform details.
        </p>
      </div>

      <div className="hospital-access__grid">
        {accessCards.map((card) => (
          <article key={card.title} className="hospital-access__card">
            <p className="hospital-access__label">{card.title}</p>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
            <Link to={card.to} className="button button--primary">
              {card.cta}
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}

function HospitalStorySection() {
  return (
    <section className="hospital-story">
      <div className="shell hospital-story__grid">
        <div className="hospital-story__overview">
          <p className="eyebrow">GoodCare Hospital</p>
          <h2>Premium care with a warm front-door experience for patients and families.</h2>
          <p className="hospital-story__lead">
            GoodCare Hospital, 24 Green Avenue, Lakeview Road, Bengaluru 560048,
            brings together modern clinical support, compassionate communication, and
            dependable emergency response in one reassuring destination.
          </p>

          <div className="hospital-story__stats">
            {hospitalStats.map((stat) => (
              <div key={stat.label} className="hospital-story__stat">
                <strong>{stat.value}</strong>
                <span>{stat.label}</span>
              </div>
            ))}
          </div>

          <div className="hospital-story__notes">
            {wellnessNotes.map((note) => (
              <div key={note} className="hospital-story__note">
                {note}
              </div>
            ))}
          </div>
        </div>

        <div className="hospital-story__side">
          <div className="hospital-story__contact-card">
            <p className="eyebrow">Emergency and helplines</p>
            <h3>Call the right team without searching around the page.</h3>
            <div className="hospital-story__contact-list">
              {helplines.map((line) => (
                <a key={line.label} href={`tel:${line.value.replace(/\s+/g, "")}`}>
                  <span>{line.label}</span>
                  <strong>{line.value}</strong>
                </a>
              ))}
            </div>
            <div className="hospital-story__ambulance">
              <strong>Ambulance support available 24/7</strong>
              <span>Rapid pickup coordination, emergency desk guidance, and admission support.</span>
            </div>
          </div>

          <div className="hospital-story__reviews">
            <p className="eyebrow">Patient reviews</p>
            {patientReviews.map((review) => (
              <article key={review.name} className="hospital-story__review">
                <div>
                  <strong>{review.name}</strong>
                  <span>{review.rating} / 5</span>
                </div>
                <p>{review.text}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function DoctorsSection() {
  return (
    <section className="hospital-doctors shell">
      <div className="section-heading">
        <p className="eyebrow">Featured doctors</p>
        <h2>Meet a few of the friendly specialists patients trust at GoodCare Hospital.</h2>
        <p>
          Short, reassuring profiles help the page feel more human and credible than a
          purely decorative marketing layout.
        </p>
      </div>

      <div className="hospital-doctors__grid">
        {doctorProfiles.map((doctor) => (
          <article key={doctor.name} className="hospital-doctors__card">
            <div className="hospital-doctors__avatar" aria-hidden="true">
              {doctor.name
                .split(" ")
                .slice(0, 2)
                .map((part) => part[0])
                .join("")}
            </div>
            <p className="hospital-doctors__specialty">{doctor.specialty}</p>
            <h3>{doctor.name}</h3>
            <p className="hospital-doctors__meta">{doctor.experience}</p>
            <div className="hospital-doctors__rating">
              <strong>{doctor.rating} / 5</strong>
              <span>Patient review score</span>
            </div>
            <p className="hospital-doctors__review">{doctor.review}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
