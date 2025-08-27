document.addEventListener("DOMContentLoaded", function () {
  const submitBtn = document.getElementById("submit-btn");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const statusMsg = document.getElementById("status-msg");

  submitBtn.addEventListener("click", function () {
    loadingIndicator.style.display = "block";
    statusMsg.innerText = "Processing... Please wait.";
  });
});

