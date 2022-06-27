////////////////////////////////////////////// Animations on scroll
AOS.init({
  duration: 1000,
  disable: "mobile"
});

////////////////////////////////////////////// Enable tooltips everywhere
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

////////////////////////////////////////////// Show up system design error modal
// replace window.onload with other event
const systemDesignError = document.getElementById("js-system-design-error");

if (systemDesignError) {
  let designError = new bootstrap.Modal(systemDesignError, {});
  window.onload = function () {
    designError.show();
  };
}


