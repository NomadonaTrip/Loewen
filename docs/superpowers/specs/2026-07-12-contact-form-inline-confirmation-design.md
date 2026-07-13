# Contact Form Inline Confirmation — Design

**Date:** 2026-07-12
**Status:** Approved

## Problem

After submitting the contact form on `contact-us.html`, visitors are navigated away
from the site to Formspree's hosted pages (reCAPTCHA challenge, then a generic
Formspree "Thanks" page). There is no on-brand confirmation that the message was
sent. Custom redirect (`_next`) is a paid Formspree feature, so a branded
thank-you-page redirect is not available on the current plan.

## Decision

AJAX-submit the form and show an inline, on-page confirmation (Approach A).
Approved over: (B) branded thank-you page via `_next` redirect — requires paid
Formspree plan; (C) keep Formspree's default page — doesn't solve the problem.

## Prerequisite (manual, dashboard)

Formspree rejects AJAX submissions while reCAPTCHA is enabled (403). The site
owner must toggle **reCAPTCHA off** in Formspree → LPW Contact Form → Settings.
Spam mitigation is replaced by a honeypot field plus Formspree's built-in
server-side spam filtering.

## Changes

### `contact-us.html`

- Add a hidden honeypot input inside the form:
  `<input type="text" name="_gotcha" ...>` — visually hidden, `tabindex="-1"`,
  `autocomplete="off"`. Bots that fill it are silently discarded by Formspree.
- Add a status element adjacent to the form with `role="status"` and
  `aria-live="polite"` so screen readers announce the outcome.
- Keep the form's existing `action="https://formspree.io/f/mojdqyvy"` and
  `method="POST"` so submission degrades gracefully to the native POST
  (Formspree hosted thanks page) if JavaScript fails.
- Extend the page's existing inline script:
  1. On submit: `preventDefault()`, disable the Send button, relabel it
     "Sending…" (prevents double submits).
  2. `fetch` POST of the `FormData` with `Accept: application/json`.
  3. Success (`response.ok`): hide the form, show confirmation message in its
     place: "Thanks, {name}! Your message has been sent. We typically reply
     within one business day."
  4. Failure (network error or non-OK): re-enable the button, preserve all
     entered values, show error message: "Sorry — something went wrong sending
     your message. Please try again, or call (519) 588-2264 or email
     robl@loewenpropertyworks.ca."

### `styles.css`

- Styles for the success and error states, matching the site's existing
  palette and typography conventions.

## Error handling

- Non-OK HTTP response and network failure both take the error path; the
  visitor's typed content is never lost.
- No-JS clients fall back to native POST → Formspree hosted flow.

## Testing

- After the reCAPTCHA toggle is off and the change is deployed: one real
  submission end-to-end (confirmation appears; message lands in the Formspree
  dashboard/inbox).
- Forced-failure check of the error path (e.g., temporarily point fetch at an
  invalid form ID locally, or submit while offline).
- No-JS fallback sanity check: form still posts natively.
