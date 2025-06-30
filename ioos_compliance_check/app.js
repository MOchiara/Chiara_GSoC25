document.addEventListener("DOMContentLoaded", function () {
      const submitBtn = document.getElementById("submit-btn");
      const loadingIndicator = document.getElementById("loadingIndicator");
      const statusMsg = document.getElementById("status-msg");

      submitBtn.addEventListener("click", function () {
        loadingIndicator.style.display = "block";
        statusMsg.innerText = "Processing... Please wait.";

        run_checker()
          .then((result) => {
            document.getElementById("report-output").textContent = result;
          })
          .catch((error) => {
            statusMsg.innerText = "An error occurred: " + error.message;
          })
          .finally(() => {
            loadingIndicator.style.display = "none";
          });
      });
    });

    function run_checker() {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve("Compliance check complete.");
        }, 2000);
      });
    }