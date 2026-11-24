const links = document.querySelectorAll(".nav-links a");

links.forEach((link) => {
  if (link.href === window.location.href) {
    link.classList.add("active");
  }
});

// "Our Services" dropdown. Without JS the submenu still opens on hover and on
// keyboard focus (CSS :focus-within); with JS the chevron button drives it via
// aria-expanded so it can also be opened by tap and closed with Escape.
document.documentElement.classList.add("js-nav");

document.querySelectorAll(".nav-dropdown").forEach((dropdown) => {
  const toggle = dropdown.querySelector(".nav-dropdown-toggle");
  const parentLink = dropdown.querySelector(":scope > a");
  if (!toggle) return;

  const setOpen = (open) => toggle.setAttribute("aria-expanded", String(open));

  toggle.addEventListener("click", () => {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  dropdown.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      toggle.focus();
    }
  });

  // Close when focus or a click lands outside the dropdown.
  dropdown.addEventListener("focusout", (event) => {
    if (!dropdown.contains(event.relatedTarget)) setOpen(false);
  });
  document.addEventListener("click", (event) => {
    if (!dropdown.contains(event.target)) setOpen(false);
  });

  // Mark "Our Services" as current when a page inside the submenu is open.
  if (dropdown.querySelector(".nav-submenu a.active") && parentLink) {
    parentLink.classList.add("active");
  }
});
