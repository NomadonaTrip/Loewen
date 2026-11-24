// Single source of truth for every "Book a service" button ([data-book]).
// To switch bookings to a Stripe Payment Link later, change this one line.
// The static href on each button is the no-JS fallback (the contact form).
const BOOKING_URL = "contact-us.html?service=windrow";

document.querySelectorAll("[data-book]").forEach((button) => {
  button.setAttribute("href", BOOKING_URL);
});
