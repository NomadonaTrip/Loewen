# Contact Form Inline Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show an on-page, on-brand confirmation (or error) message when a visitor submits the contact form, instead of navigating them away to Formspree's hosted pages.

**Architecture:** Progressive enhancement on the existing static page. The form keeps its native `action`/`method` (no-JS fallback). An inline script intercepts submit, POSTs via `fetch` with `Accept: application/json`, and toggles a pre-existing accessible status element between success and error states. A hidden `_gotcha` honeypot replaces reCAPTCHA for spam control.

**Tech Stack:** Plain HTML/CSS/vanilla JS. No build step, no dependencies. Backend is Formspree form `https://formspree.io/f/mojdqyvy`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-12-contact-form-inline-confirmation-design.md`
- Form action MUST remain `https://formspree.io/f/mojdqyvy` with `method="POST"` (no-JS fallback).
- Success copy (exact): `Thanks, {name}! Your message has been sent. We typically reply within one business day.` — when name is blank, omit `, {name}`.
- Error copy (exact): `Sorry — something went wrong sending your message. Please try again, or call (519) 588-2264 or email robl@loewenpropertyworks.ca.`
- On error, the visitor's typed values must be preserved and the Send button re-enabled.
- Site is dark-themed: body is `var(--primary-dark)` (#000000). Palette variables: `--secondary-dark: #32373c`, `--text-light: #ffffff`, `--text-cream: #f5ecd5`, `--text-green: #578e7e`, `--accent-green: #183d3d`.
- GOTCHA: `.contact-us-form form { display: flex; }` in `styles.css` overrides the HTML `hidden` attribute. Hide the form with `contactForm.style.display = "none"`, never with `hidden`.
- This repo has no test framework; each task verifies in a real browser via a local HTTP server and the Playwright MCP tools.
- Manual prerequisite (site owner, not this plan): disable reCAPTCHA in Formspree → LPW Contact Form → Settings. Until that is done, real submissions via fetch return 403 — local verification therefore stubs `fetch`.

---

### Task 1: Form markup — honeypot and status element

**Files:**
- Modify: `contact-us.html:195-205` (the `.contact-us-form` div)

**Interfaces:**
- Produces: `<form id="contact-form">`, `<div id="form-status">` — Task 2 styles `#form-status` and the classes `form-status-success` / `form-status-error`; Task 3's script targets both ids.

- [ ] **Step 1: Replace the form block**

In `contact-us.html`, replace:

```html
      <div class="contact-us-form">
        <form action="https://formspree.io/f/mojdqyvy" method="POST">
          <label for="name">Name:</label>
          <input type="text" id="name" name="name" required />
          <label for="email">Email:</label>
          <input type="email" id="email" name="email" required />
          <label for="message">Message:</label>
          <textarea id="message" name="message" rows="4" required></textarea>
          <button type="submit">Send</button>
        </form>
      </div>
```

with:

```html
      <div class="contact-us-form">
        <form
          action="https://formspree.io/f/mojdqyvy"
          method="POST"
          id="contact-form"
        >
          <label for="name">Name:</label>
          <input type="text" id="name" name="name" required />
          <label for="email">Email:</label>
          <input type="email" id="email" name="email" required />
          <label for="message">Message:</label>
          <textarea id="message" name="message" rows="4" required></textarea>
          <input
            type="text"
            name="_gotcha"
            style="display: none"
            tabindex="-1"
            autocomplete="off"
            aria-hidden="true"
          />
          <button type="submit">Send</button>
        </form>
        <div id="form-status" role="status" aria-live="polite"></div>
      </div>
```

- [ ] **Step 2: Verify in browser**

```bash
python3 -m http.server 8788 --directory "/mnt/e/TOOLMAKER/WEB PROJECTS/Loewen" &
```

With Playwright MCP: `browser_navigate` to `http://localhost:8788/contact-us.html`, take `browser_snapshot`.
Expected: form renders unchanged visually; the `_gotcha` input is NOT visible; no `#form-status` content visible.

- [ ] **Step 3: Commit**

```bash
git add contact-us.html
git commit -m "Add honeypot field and accessible status element to contact form"
```

---

### Task 2: Status message styles

**Files:**
- Modify: `styles.css` (append after the `form button:hover` rule, ~line 1970)

**Interfaces:**
- Consumes: `#form-status` element from Task 1.
- Produces: classes `form-status-success`, `form-status-error` used by Task 3's script.

- [ ] **Step 1: Append status styles to `styles.css`**

```css
/* Contact form: inline submission status messages */
#form-status {
  display: none;
  padding: 16px 20px;
  margin-top: 16px;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text-light);
  border-left: 4px solid;
  box-sizing: border-box;
}
#form-status.form-status-success {
  display: block;
  background-color: var(--accent-green);
  border-color: var(--text-green);
}
#form-status.form-status-error {
  display: block;
  background-color: #3d1818;
  border-color: #8e5757;
}
```

- [ ] **Step 2: Verify in browser**

With Playwright MCP on `http://localhost:8788/contact-us.html`, run `browser_evaluate`:

```js
() => {
  const s = document.getElementById("form-status");
  s.className = "form-status-success";
  s.textContent = "Thanks, Test! Your message has been sent. We typically reply within one business day.";
}
```

Take `browser_take_screenshot`. Expected: dark-green box with lighter green left border and white text below the form, matching the site's palette. Repeat with `form-status-error`: expected dark-red box with muted red left border.

- [ ] **Step 3: Commit**

```bash
git add styles.css
git commit -m "Style contact form success and error status messages"
```

---

### Task 3: AJAX submit handler

**Files:**
- Modify: `contact-us.html` (extend the existing inline `<script>` block that handles the hamburger menu, before `</script>`)

**Interfaces:**
- Consumes: `#contact-form`, `#form-status` (Task 1); `form-status-success` / `form-status-error` classes (Task 2).

- [ ] **Step 1: Append handler to the existing inline script in `contact-us.html`**

Add after the existing "Close menu when a link is clicked" block, inside the same `<script>` tag:

```js
      // Contact form: AJAX submit with inline confirmation
      const contactForm = document.getElementById("contact-form");
      const formStatus = document.getElementById("form-status");

      contactForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const submitButton = contactForm.querySelector(
          "button[type='submit']",
        );
        submitButton.disabled = true;
        submitButton.textContent = "Sending…";
        try {
          const response = await fetch(contactForm.action, {
            method: "POST",
            body: new FormData(contactForm),
            headers: { Accept: "application/json" },
          });
          if (!response.ok) {
            throw new Error("Formspree responded " + response.status);
          }
          const name = document.getElementById("name").value.trim();
          contactForm.style.display = "none";
          formStatus.className = "form-status-success";
          formStatus.textContent =
            "Thanks" +
            (name ? ", " + name : "") +
            "! Your message has been sent. We typically reply within one business day.";
        } catch (error) {
          submitButton.disabled = false;
          submitButton.textContent = "Send";
          formStatus.className = "form-status-error";
          formStatus.textContent =
            "Sorry — something went wrong sending your message. Please try again, or call (519) 588-2264 or email robl@loewenpropertyworks.ca.";
        }
      });
```

- [ ] **Step 2: Verify success path (stubbed fetch)**

With Playwright MCP on `http://localhost:8788/contact-us.html`:

1. `browser_evaluate`: `() => { window.fetch = async () => ({ ok: true }); }`
2. `browser_fill_form`: Name = `Test`, Email = `test@example.com`, Message = `Hello`
3. Click Send.
4. `browser_snapshot`.

Expected: form is gone; green status box reads `Thanks, Test! Your message has been sent. We typically reply within one business day.`

- [ ] **Step 3: Verify error path (stubbed fetch failure)**

Reload the page, then:

1. `browser_evaluate`: `() => { window.fetch = async () => ({ ok: false, status: 404 }); }`
2. Fill Name = `Test`, Email = `test@example.com`, Message = `Hello`; click Send.
3. `browser_snapshot`.

Expected: form still visible with all typed values intact; Send button enabled and labelled `Send`; red status box shows the exact error copy including phone and email.

- [ ] **Step 4: Verify no-JS fallback markup**

```bash
grep -n 'action="https://formspree.io/f/mojdqyvy"' contact-us.html
grep -n 'method="POST"' contact-us.html
```

Expected: both present (native POST fallback intact).

- [ ] **Step 5: Commit**

```bash
git add contact-us.html
git commit -m "Show inline confirmation after contact form submission"
```

---

### Post-deploy verification (manual, after site owner acts)

Not a code task — record of what must happen after this plan ships:

1. Site owner disables reCAPTCHA: Formspree → LPW Contact Form → Settings.
2. Site owner pushes/deploys.
3. One real submission from https://loewenpropertyworks.ca/contact-us.html: expect the inline green confirmation (no navigation away) and the message arriving in the Formspree dashboard/inbox.
