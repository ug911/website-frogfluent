# FrogFluent — Tutor Marketplace

A static marketing site for FrogFluent, the language-tutor marketplace, integrated
end-to-end with the [Wise](https://wise.live/) backend (`frogfluent-sample`
namespace). The site lists tutors, lets students book free trials inline, and
runs the paid 1:1 session purchase through Wise's payment flow.

There's no app server — the site is a handful of static HTML pages plus a small
amount of vanilla JS that talks directly to Wise's public APIs.

## What's in here

```
.
├── index.html              # Home (built by build.py)
├── tutors.html             # Tutor listing (built)
├── tutor-details.html      # Single-tutor detail page template (built)
├── about.html / contact.html / become-tutor.html
├── payment_status.html     # Stripe / payment-gateway return page
│
├── styles.css              # All site styles
├── tutors-loader.js        # Renders tutor card grids from tutors-data.json
├── tutor-detail.js         # Renders the detail page, handles Pay & callback
├── booking-widget.js       # Native inline scheduler (replaces Wise iframe)
│
├── build.py                # Static-site generator. Re-run after edits
├── onboard_tutors.py       # One-shot script that creates the 12 tutors in Wise
├── fetch_course_data.py    # Pulls per-course public data into tutors-data.json
├── serve.py                # Local dev server with /payment_status rewrite + optional SSL
├── vercel.json             # Production rewrite + cache headers
│
├── assets/
│   ├── tutors-data.json    # Live tutor data the JS loads at runtime
│   └── ...                 # Logos, flags, hero images, etc.
│
├── onboard_results.json    # Wise IDs for each tutor (teacher_id, class_id, demo_class_id)
├── tutors.json             # Scraped tutor list (input to onboard_tutors.py)
├── .env                    # Local-only secrets (gitignored)
└── .env.example
```

## Architecture

### Browser → Wise APIs (no backend)

All dynamic behaviour happens client-side against `api.wiseapp.live`. Two keys
make this work:

- `x-api-key: web:...` — public web key, safe to ship in JS
- `x-wise-namespace: frogfluent-sample`

The site never proxies these calls — the user's browser talks straight to
Wise.

```
Browser ── GET  /assets/tutors-data.json       (this repo)
       ── GET  /public/demoRooms?slug=...     (Wise — list slots)
       ── POST /public/demoRooms/:id/session  (Wise — book a free trial)
       ── POST /public/classes/:id/initiateFeePayment
       ── (redirect to Stripe checkout)
       ── (Stripe returns to /payment_status/:orderId)
       ── GET  /api/v1/payments/payment_order/:id/callback  (Wise — verify)
       ── (redirect back to /tutor-details.html?...&payment_status=success)
```

### Build pipeline

`build.py` is the only thing that touches HTML. It composes shared
header/footer/inline-CSS with per-page bodies and writes the five pages above.
Run it after any HTML/CSS change:

```bash
python3 build.py
```

`tutors-data.json` is refreshed from the live Wise instance with:

```bash
python3 fetch_course_data.py
```

## Local development

Requirements: Python 3.9+, `requests`, `beautifulsoup4` (only for the scripts —
the site itself has zero dependencies).

```bash
pip3 install --break-system-packages requests beautifulsoup4
cp .env.example .env       # then fill in WISE_BEARER_TOKEN
python3 build.py           # generate HTML
python3 serve.py 8099      # http://localhost:8099/
```

For the full payment loop (Stripe forces HTTPS on `returnURL`):

```bash
python3 serve.py 8099 --ssl     # https://localhost:8099/
```

A self-signed cert is generated into `.certs/` on first run. Accept the cert
warning in Chrome once.

### What `serve.py` does that plain `python3 -m http.server` doesn't

- Rewrites `/payment_status/<orderId>` → `/payment_status.html` so Stripe's
  redirect back lands on a real file. The same rewrite is configured for
  production in `vercel.json`.
- Optionally serves over HTTPS with a self-signed cert (`--ssl`) for end-to-end
  payment testing.

## Deploying to Vercel

The project is a static site so Vercel deploys with no build step.

1. Push to GitHub (already done — `ug911/website-frogfluent`).
2. In Vercel, **Add New → Project**, import the repo.
3. **Framework Preset:** Other. **Build Command:** leave blank. **Output
   Directory:** leave blank (root).
4. **Environment Variables:** none needed at deploy time. The bearer in `.env`
   is only used by the onboarding scripts which run locally — the public site
   doesn't need it.
5. Deploy.

`vercel.json` already wires up:
- The `/payment_status/:orderId` rewrite (same behaviour as `serve.py`).
- A 1-hour cache on `/assets/*`.

### Pointing Stripe / Wise to the deployed domain

After Vercel gives you a domain (e.g. `frogfluent.vercel.app` or a custom
domain), nothing in the code needs to change — the `returnURL` for
`initiateFeePayment` is built dynamically from `location.origin` in
`tutor-detail.js`, so it picks up the production URL automatically.

## Updating tutor data

If a tutor's bio / price / availability changes on the Wise side:

```bash
python3 fetch_course_data.py    # writes assets/tutors-data.json
git commit -am "Refresh tutor data"
git push                         # Vercel auto-deploys
```

## Onboarding more tutors

`onboard_tutors.py` is a one-shot script that:

1. Scrapes tutors from `frogfluent.com`
2. For each tutor in Wise: invites a teacher, uploads photo, sets payout,
   creates a public profile, a paid 1:1 class, a free DEMO room, and adds
   the class to the public store.

```bash
python3 onboard_tutors.py --dry-run      # preview API calls
python3 onboard_tutors.py                # run live (requires WISE_BEARER_TOKEN)
python3 onboard_tutors.py --photos-only  # re-attach photos only
```

Edge cases (idempotency on re-run, bio truncation, payment-option lookup) are
documented as inline comments at each step.

## Secrets

- `.env` (gitignored) holds `WISE_BEARER_TOKEN`, used only by the local
  onboarding scripts. The deployed site never reads it.
- The `x-api-key: web:aff7589260...` value in `booking-widget.js` and
  `onboard_tutors.py` is Wise's public web client key — it's deliberately
  visible in browser JS and is not a secret.
- If `WISE_BEARER_TOKEN` ever leaks, rotate it from the Wise admin dashboard.

## Booking flow notes

Wise's hosted `/book/<slug>` page can't be cleanly iframed from a third-party
domain (third-party-cookie blocks cause "Demo not found!" after the SPA tries
to read its session). Instead, `booking-widget.js` calls Wise's
`/public/demoRooms` + `/public/demoRooms/:id/session` endpoints directly and
renders a native calendar + slot picker. This gives an inline experience while
still using exactly the same backend Wise's own UI uses.
