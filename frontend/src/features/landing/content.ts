export const landingSlides = [
  {
    eyebrow: "Compassionate care",
    title: "GoodCare Hospital makes every visit feel calmer, clearer, and more human.",
    body:
      "From first consultation to follow-up support, our teams focus on kind communication, trusted specialists, and smooth patient guidance.",
    accent: "sunrise",
    statLabel: "Patient satisfaction",
    statValue: "4.9/5",
    quote: "Healing begins when patients feel heard.",
  },
  {
    eyebrow: "24/7 emergency response",
    title: "Fast ambulance coordination and emergency helplines are always within reach.",
    body:
      "Dedicated rapid-response support, critical-care readiness, and simple contact points help families act quickly during urgent situations.",
    accent: "deep-sea",
    statLabel: "Average response desk",
    statValue: "2 min",
    quote: "Care should be immediate when every second matters.",
  },
  {
    eyebrow: "Trusted doctors",
    title: "Experienced specialists guide care plans with warmth and confidence.",
    body:
      "Meet approachable doctors across cardiology, neurology, pediatrics, orthopedics, and women's health in one coordinated hospital experience.",
    accent: "twilight",
    statLabel: "Specialist teams",
    statValue: "18+",
    quote: "Expert care feels better when it also feels personal.",
  },
  {
    eyebrow: "Simple patient access",
    title: "Login and registration stay easy, so patients can focus on care instead of forms.",
    body:
      "A clean sign-in path for returning patients and a straightforward registration journey for first-time visitors keeps the homepage focused and welcoming.",
    accent: "aurora",
    statLabel: "Registration journey",
    statValue: "3 steps",
    quote: "The best digital experiences remove stress, not add to it.",
  },
  {
    eyebrow: "Community trust",
    title: "Thousands of families choose GoodCare Hospital for dependable treatment and support.",
    body:
      "Positive patient stories, transparent help lines, and a polished front-door experience build trust before a visitor even books a consultation.",
    accent: "violet-mist",
    statLabel: "Families served",
    statValue: "52,000+",
    quote: "Trust grows through consistency, kindness, and clinical excellence.",
  },
  {
    eyebrow: "Healthy living",
    title: "Preventive guidance, recovery support, and hopeful messaging belong on a hospital homepage.",
    body:
      "Healthy quotes, friendly doctor introductions, and clear service highlights give the website the reassuring tone people expect from a modern hospital.",
    accent: "golden-hour",
    statLabel: "Recovery follow-ups",
    statValue: "98%",
    quote: "A healthier tomorrow starts with one confident step today.",
  },
] as const;

export const accessCards = [
  {
    title: "Login",
    description:
      "Returning patients can quickly enter their account to continue their care journey.",
    to: "/login",
    cta: "Open Login",
  },
  {
    title: "Registration",
    description:
      "New patients can create their account and get started with a clean, guided sign-up flow.",
    to: "/patient/register",
    cta: "Start Registration",
  },
] as const;

export const hospitalStats = [
  { value: "52,000+", label: "Patients treated" },
  { value: "4.9/5", label: "Average patient rating" },
  { value: "18+", label: "Specialty departments" },
  { value: "24/7", label: "Emergency ambulance line" },
] as const;

export const helplines = [
  { label: "Emergency", value: "+91 1800 300 9111" },
  { label: "Ambulance", value: "+91 1800 300 9222" },
  { label: "Appointment desk", value: "+91 1800 300 9333" },
  { label: "Women's care helpline", value: "+91 1800 300 9444" },
] as const;

export const patientReviews = [
  {
    name: "Riya Sharma",
    rating: "5.0",
    text: "The doctors explained everything patiently and the staff made my mother's treatment journey feel safe and organized.",
  },
  {
    name: "Aditya Verma",
    rating: "4.9",
    text: "From the first call to discharge support, the experience felt premium, calm, and genuinely caring.",
  },
  {
    name: "Neha Bhatia",
    rating: "5.0",
    text: "The emergency response team was quick, reassuring, and highly professional when our family needed immediate help.",
  },
] as const;

export const doctorProfiles = [
  {
    name: "Dr. Aarav Mehta",
    specialty: "Cardiology",
    experience: "14 years experience",
    rating: "4.9",
    review: "Known for calm consultations and clear heart-health guidance.",
  },
  {
    name: "Dr. Sana Kapoor",
    specialty: "Neurology",
    experience: "11 years experience",
    rating: "4.8",
    review: "Praised by families for thoughtful diagnosis and follow-up care.",
  },
  {
    name: "Dr. Vikram Nair",
    specialty: "Orthopedics",
    experience: "13 years experience",
    rating: "4.9",
    review: "Trusted for recovery planning, mobility treatment, and patient comfort.",
  },
  {
    name: "Dr. Meera Joshi",
    specialty: "Pediatrics",
    experience: "10 years experience",
    rating: "5.0",
    review: "Loved by parents for warm communication and child-friendly treatment.",
  },
] as const;

export const wellnessNotes = [
  "Your health deserves clarity, comfort, and compassionate expertise.",
  "Good care is not only about treatment. It is also about trust, timing, and thoughtful guidance.",
  "A confident recovery starts with the right doctor, the right support, and the right environment.",
] as const;
