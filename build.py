#!/usr/bin/env python3
"""Build static pages from a layout + per-page body files."""
from pathlib import Path

ROOT = Path(__file__).parent
CSS = (ROOT / "styles.css").read_text()

NAV_ITEMS = [
    ("index.html", "Home"),
    ("tutors.html", "Find tutors"),
    ("about.html", "About us"),
    ("contact.html", "Contact us"),
    ("become-tutor.html", "Become a tutor"),
]

def nav_html(active):
    parts = []
    for href, label in NAV_ITEMS:
        cls = ' class="active"' if href == active else ""
        parts.append(f'<a href="{href}"{cls}>{label}</a>')
    return "\n      ".join(parts)

def page(title, active, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title} — FrogFluent</title>
<link rel="icon" href="assets/logo.svg" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css" />
<style>{CSS}</style>
{extra_head}
</head>
<body>

<header class="site-header">
  <div class="container header-inner">
    <a href="index.html" class="logo"><img src="assets/logo.svg" alt="FrogFluent" /></a>
    <nav class="main-nav">
      {nav_html(active)}
    </nav>
    <div class="header-actions">
      <a href="#" class="btn btn-outline">Tutor Login</a>
      <a href="#" class="btn btn-primary">Student Login</a>
    </div>
    <button class="mobile-toggle" aria-label="Menu">☰</button>
  </div>
</header>

{body}

<footer class="site-footer">
  <div class="container footer-grid">
    <div class="f-col about">
      <img src="assets/img/footer-logo.svg" alt="FrogFluent" class="footer-logo"/>
      <p>FrogFluent connects learners with passionate language tutors worldwide. Pick a language, meet a tutor, and start speaking.</p>
    </div>
    <div class="f-col">
      <h5>Quick Links</h5>
      <ul>
        <li><a href="index.html">Home</a></li>
        <li><a href="tutors.html">Find tutors</a></li>
        <li><a href="about.html">About us</a></li>
        <li><a href="contact.html">Contact us</a></li>
        <li><a href="become-tutor.html">Become a tutor</a></li>
      </ul>
    </div>
    <div class="f-col">
      <h5>Contact</h5>
      <ul class="contact-list">
        <li>📞 +91 77150 80455</li>
        <li>✉ admin@frogfluent.com</li>
        <li>📍 Thane, Maharashtra, India</li>
      </ul>
    </div>
  </div>
  <img class="f-shape f-shape-1" src="assets/img/fw-cartoon-4.png" alt=""/>
  <img class="f-shape f-shape-2" src="assets/img/fw-cartoon-5.png" alt=""/>
  <div class="copyright">
    <div class="container">© 2026 FrogFluent. All rights reserved.</div>
  </div>
</footer>

<script src="booking-widget.js"></script>
<script src="tutors-loader.js"></script>
<script>
  document.querySelector('.mobile-toggle')?.addEventListener('click', () => {{
    document.querySelector('.main-nav')?.classList.toggle('open');
    document.querySelector('.header-actions')?.classList.toggle('open');
  }});
</script>
</body>
</html>
"""

# ---------- HOME ----------
home_body = """
<section class="hero">
  <div class="container hero-grid">
    <div class="hero-text">
      <span class="eyebrow">Welcome, Guest · <a href="#">Sign up / Sign in</a></span>
      <h1>Take 3 Free Trials <span class="underline-word">No Strings<img src="assets/img/underline-hero.svg" alt=""/></span> Attached</h1>
      <p>Explore our platform with zero commitment. Pick a language, meet a tutor, and try three sessions on us — no card, no catch.</p>
      <div class="hero-cta">
        <a href="tutors.html" class="btn btn-primary btn-lg">Find a Tutor</a>
        <a href="become-tutor.html" class="btn btn-ghost btn-lg">Become a Tutor →</a>
      </div>
      <ul class="hero-points">
        <li>✓ Up to 3 free trial sessions</li>
        <li>✓ Personalized learning</li>
        <li>✓ Global tutors</li>
      </ul>
    </div>
    <div class="hero-visual">
      <img class="hero-img-1" src="assets/img/hero-section1.webp" alt="Tutor"/>
      <img class="hero-img-2" src="assets/img/hero-section2.webp" alt="Student"/>
    </div>
  </div>
</section>

<section class="section languages">
  <div class="container">
    <div class="section-head center">
      <span class="kicker">Languages</span>
      <h2>I Want To <span class="underline-word">Learn<img src="assets/img/underline-category.svg" alt=""/></span></h2>
      <p>Choose a language and start your journey with native and certified tutors.</p>
    </div>
    <div class="lang-grid">
      <a href="tutors.html?lang=german" class="lang-card"><div class="flag"><img src="assets/flags/german.jpg" alt="German"/></div><h3>German</h3><p>13 Teachers</p></a>
      <a href="tutors.html?lang=french" class="lang-card"><div class="flag"><img src="assets/flags/france.jpg" alt="French"/></div><h3>French</h3><p>1 Teacher</p></a>
      <a href="#" class="lang-card disabled"><div class="flag"><img src="assets/flags/spain.jpg" alt="Spanish"/></div><h3>Spanish</h3><p>Coming soon</p></a>
      <a href="#" class="lang-card disabled"><div class="flag"><img src="assets/flags/italy.jpg" alt="Italian"/></div><h3>Italian</h3><p>Coming soon</p></a>
    </div>
  </div>
</section>

<section class="section tutors-section">
  <div class="container">
    <div class="section-head center">
      <span class="kicker">Featured Tutors</span>
      <h2>Meet Our <span class="underline-word">Tutors<img src="assets/img/underline-team.svg" alt=""/></span></h2>
      <p>Hand-picked teachers who bring patience, structure, and real conversation to every lesson.</p>
    </div>
    <div class="tutor-grid" data-tutor-grid data-limit="3">
      <p class="loading">Loading tutors...</p>
    </div>
  </div>
</section>

<section class="section benefits">
  <div class="container">
    <div class="benefit-grid">
      <div class="benefit"><img src="assets/img/funfact-1.svg" alt=""/><h4>Learn from experts</h4><p>Verified, certified, and reviewed tutors.</p></div>
      <div class="benefit"><img src="assets/img/funfact-2.svg" alt=""/><h4>Curated lessons</h4><p>Plans built around your level and goals.</p></div>
      <div class="benefit"><img src="assets/img/funfact-3.svg" alt=""/><h4>Relevant vocabulary</h4><p>Phrases and words you'll actually use.</p></div>
      <div class="benefit"><img src="assets/img/funfact-4.svg" alt=""/><h4>Individual focus</h4><p>1‑on‑1 attention that fits your pace.</p></div>
    </div>
  </div>
</section>

<section class="section why-enroll">
  <div class="container two-col">
    <div class="col-img"><img src="assets/img/why-enroll.png" alt="Why enroll"/></div>
    <div class="col-text">
      <span class="kicker">Why Enroll</span>
      <h2>A platform built around <span class="underline-word">you<img src="assets/img/underline-cta.svg" alt=""/></span></h2>
      <ul class="check-list">
        <li>Up to 3 free trial sessions</li>
        <li>Personalized learning for all levels</li>
        <li>Access to global tutors</li>
        <li>Interactive student community programs and events</li>
      </ul>
      <a href="tutors.html" class="btn btn-primary">Get started</a>
    </div>
  </div>
</section>

<section class="section testimonials">
  <div class="container">
    <div class="section-head center">
      <span class="kicker">Testimonials</span>
      <h2>What students <span class="underline-word">say<img src="assets/img/underline-testimonial.svg" alt=""/></span></h2>
    </div>
    <div class="testimonial-grid">
      <figure class="t-card"><img class="avatar" src="assets/testimonials/t1.png" alt=""/><blockquote>Frog Fluent made learning a new language so much fun! The lessons are super interactive, and I felt confident speaking within just a few weeks.</blockquote><figcaption><strong>Ananya Banerjee</strong><span>Student</span></figcaption></figure>
      <figure class="t-card"><img class="avatar" src="assets/testimonials/t2.png" alt=""/><blockquote>Before Frog Fluent, I struggled to stay motivated. But this platform kept me hooked with its unique teaching style and real‑life practice sessions.</blockquote><figcaption><strong>Vivaan Singh</strong><span>Student</span></figcaption></figure>
      <figure class="t-card"><img class="avatar" src="assets/testimonials/t3.png" alt=""/><blockquote>What I loved most is how personalized everything felt. The platform understood my pace, corrected my mistakes gently, and helped me grow confidence.</blockquote><figcaption><strong>Rahul Nair</strong><span>Student</span></figcaption></figure>
      <figure class="t-card"><img class="avatar" src="assets/testimonials/t4.png" alt=""/><blockquote>I joined Frog Fluent to improve my English, but I ended up learning much more—confidence, communication, and cultural awareness.</blockquote><figcaption><strong>Ishita Sharma</strong><span>Student</span></figcaption></figure>
      <figure class="t-card"><img class="avatar" src="assets/testimonials/t1.png" alt=""/><blockquote>The way Frog Fluent teaches is unlike anything else. It's not boring grammar drills, but real conversations and smart tools that actually make you fluent.</blockquote><figcaption><strong>Aarav Mehta</strong><span>Student</span></figcaption></figure>
    </div>
  </div>
</section>
"""

# ---------- TUTORS ----------
tutors_data = [
    ("Maria Konovalenko", "Germany", "German", "tutor1.jpg", "Builds confidence with interactive lessons tailored to your everyday goals.", "4.9", "$18/hr"),
    ("Maximilian Sauerland", "Germany", "German", "tutor2.jpg", "Structured grammar and conversational fluency for beginners to advanced learners.", "4.9", "$22/hr"),
    ("Jean Martial KOFFI", "Ivory Coast", "German", "tutor3.jpg", "Patient teacher blending culture, vocabulary, and real-world practice.", "4.9", "$15/hr"),
    ("Maria Konovalenko", "Germany", "German", "tutor1.jpg", "A1 to C1 — exam prep, business German, and conversation.", "4.8", "$20/hr"),
    ("Maximilian Sauerland", "Germany", "German", "tutor2.jpg", "Native speaker focused on pronunciation and listening skills.", "4.9", "$24/hr"),
    ("Jean Martial KOFFI", "Ivory Coast", "French", "tutor3.jpg", "Conversational French with cultural immersion and travel-ready vocabulary.", "5.0", "$16/hr"),
]
tutor_cards = '<p class="loading">Loading tutors from Wise…</p>'
tutors_body = f"""
<section class="page-hero">
  <div class="container">
    <span class="kicker">Find Tutors</span>
    <h1>Pick a tutor and book a <span class="underline-word">free trial<img src="assets/img/underline-team.svg" alt=""/></span></h1>
    <p>Filter by language, price, or availability. Every tutor offers up to 3 free trial sessions.</p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="tutor-filters">
      <select><option>All languages</option><option>German</option><option>French</option></select>
      <select><option>Any price</option><option>$10–$20</option><option>$20–$30</option></select>
      <select><option>Any rating</option><option>4.5+</option><option>4.8+</option></select>
      <input type="search" placeholder="Search tutor name…"/>
      <button class="btn btn-primary">Search</button>
    </div>
    <div class="tutor-grid four" data-tutor-grid>
      {tutor_cards}
    </div>
  </div>
</section>
"""

# ---------- ABOUT ----------
about_body = """
<section class="page-hero">
  <div class="container">
    <span class="kicker">About</span>
    <h1>We believe languages <span class="underline-word">open doors<img src="assets/img/underline-cta.svg" alt=""/></span></h1>
    <p>FrogFluent is a marketplace where curious learners meet passionate teachers — globally, affordably, and at their own pace.</p>
  </div>
</section>

<section class="section">
  <div class="container two-col">
    <div class="col-img"><img src="assets/img/why-enroll.png" alt="About"/></div>
    <div class="col-text">
      <span class="kicker">Our Story</span>
      <h2>Built for real conversations, not grammar drills</h2>
      <p>We started FrogFluent because traditional language apps stopped short of what really matters: speaking. Our platform pairs you with vetted human tutors who shape lessons around your goals — travel, work, exams, or curiosity.</p>
      <ul class="check-list">
        <li>Hand-picked native and certified tutors</li>
        <li>Flexible scheduling across global time zones</li>
        <li>Transparent pricing — no subscriptions</li>
        <li>Up to 3 free trial sessions</li>
      </ul>
    </div>
  </div>
</section>

<section class="section benefits">
  <div class="container">
    <div class="section-head center"><span class="kicker">Our Values</span><h2>What we stand for</h2></div>
    <div class="benefit-grid">
      <div class="benefit"><img src="assets/img/funfact-1.svg" alt=""/><h4>Quality</h4><p>Every tutor goes through screening and student reviews.</p></div>
      <div class="benefit"><img src="assets/img/funfact-2.svg" alt=""/><h4>Curiosity</h4><p>Learning is most fun when it's personal.</p></div>
      <div class="benefit"><img src="assets/img/funfact-3.svg" alt=""/><h4>Access</h4><p>Affordable rates, global tutors, zero gatekeeping.</p></div>
      <div class="benefit"><img src="assets/img/funfact-4.svg" alt=""/><h4>Community</h4><p>Events, groups, and exchanges to keep you practicing.</p></div>
    </div>
  </div>
</section>
"""

# ---------- CONTACT ----------
contact_body = """
<section class="page-hero">
  <div class="container">
    <span class="kicker">Contact</span>
    <h1>We'd love to <span class="underline-word">hear from you<img src="assets/img/underline-hero.svg" alt=""/></span></h1>
    <p>Questions about tutors, pricing, or partnerships? Drop us a line — we usually reply within a day.</p>
  </div>
</section>

<section class="section">
  <div class="container two-col">
    <div class="col-text contact-info">
      <h3>Reach us</h3>
      <ul class="contact-list big">
        <li><strong>Phone</strong><span>+91 77150 80455</span></li>
        <li><strong>Email</strong><span>admin@frogfluent.com</span></li>
        <li><strong>Address</strong><span>Thane, Maharashtra, India</span></li>
        <li><strong>Hours</strong><span>Mon–Sat, 9am – 7pm IST</span></li>
      </ul>
    </div>
    <form class="contact-form" onsubmit="event.preventDefault();alert('Thanks! We will be in touch.');">
      <h3>Send a message</h3>
      <div class="row two"><input required placeholder="First name"/><input required placeholder="Last name"/></div>
      <input required type="email" placeholder="Email"/>
      <input placeholder="Subject"/>
      <textarea required rows="5" placeholder="Your message…"></textarea>
      <button class="btn btn-primary" type="submit">Send message</button>
    </form>
  </div>
</section>
"""

# ---------- BECOME TUTOR ----------
become_body = """
<section class="page-hero">
  <div class="container">
    <span class="kicker">Become a Tutor</span>
    <h1>Teach what you love, <span class="underline-word">anytime, anywhere<img src="assets/img/underline-cta.svg" alt=""/></span></h1>
    <p>Join a growing community of educators reaching motivated learners around the world.</p>
  </div>
</section>

<section class="section">
  <div class="container two-col reverse">
    <div class="col-text">
      <span class="kicker">Why teach with us</span>
      <h2>Built for teachers, not platforms</h2>
      <div class="tutor-perks">
        <div class="perk"><img src="assets/icons/tutor1.svg" alt=""/><h4>Remote</h4><p>Teach from anywhere.</p></div>
        <div class="perk"><img src="assets/icons/tutor2.svg" alt=""/><h4>Rewarding</h4><p>Shape real learners' journeys.</p></div>
        <div class="perk"><img src="assets/icons/tutor3.svg" alt=""/><h4>Well paid</h4><p>Transparent, on-time payouts.</p></div>
      </div>
      <ul class="check-list">
        <li>Set your own hourly rate</li>
        <li>Choose your schedule, week by week</li>
        <li>Tools for lessons, homework, and progress tracking</li>
        <li>Get paid in your local currency</li>
      </ul>
    </div>
    <div class="col-img"><img src="assets/img/become-tutor.png" alt="Become a tutor"/></div>
  </div>
</section>

<section class="section apply-section">
  <div class="container narrow">
    <div class="section-head center"><span class="kicker">Apply</span><h2>Start your application</h2><p>Tell us about yourself. We'll review and reach out within 3–5 business days.</p></div>
    <form class="contact-form full" onsubmit="event.preventDefault();alert('Thanks! Your application has been received.');">
      <div class="row two"><input required placeholder="Full name"/><input required type="email" placeholder="Email"/></div>
      <div class="row two"><input required placeholder="Country"/><input required placeholder="Languages you teach"/></div>
      <input required placeholder="Years of teaching experience"/>
      <textarea required rows="5" placeholder="Tell us about your teaching style…"></textarea>
      <button class="btn btn-primary btn-lg" type="submit">Submit application</button>
    </form>
  </div>
</section>
"""

# ---------- TUTOR DETAILS ----------
tutor_detail_body = """
<section class="tutor-detail" data-tutor-detail>
  <div class="container">
    <p class="loading">Loading tutor…</p>
  </div>
</section>
<script src="tutor-detail.js"></script>
"""

# Write
pages = {
    "index.html": ("Learn Languages with Expert Tutors", "index.html", home_body),
    "tutors.html": ("Find Tutors", "tutors.html", tutors_body),
    "about.html": ("About Us", "about.html", about_body),
    "contact.html": ("Contact Us", "contact.html", contact_body),
    "become-tutor.html": ("Become a Tutor", "become-tutor.html", become_body),
    "tutor-details.html": ("Tutor Profile", "tutors.html", tutor_detail_body),
}
for filename, (title, active, body) in pages.items():
    (ROOT / filename).write_text(page(title, active, body))
    print("wrote", filename)
