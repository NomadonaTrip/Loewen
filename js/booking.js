// Single source of truth for every "Book a service" button ([data-book]).
// Booking is one e-Transfer, explained on windrow-clearing-booked.html.
// To switch bookings to a Stripe Payment Link later, change this one line.
// The static href on each button is the same page, for visitors without JS.
const BOOKING_URL = "windrow-clearing-booked.html";

document.querySelectorAll("[data-book]").forEach((button) => {
  button.setAttribute("href", BOOKING_URL);
});
