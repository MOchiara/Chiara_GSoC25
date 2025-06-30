document.addEventListener("DOMContentLoaded", () => {
  const runQcBtn = document.getElementById("runQcBtn");
  const loader = document.getElementById("loadingIndicator");

  runQcBtn.addEventListener("click", () => {
    if (loader) {
      loader.style.display = "block";
    }
  });
});
