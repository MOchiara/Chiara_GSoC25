function populate_dropdown(checkers) {
  const select = document.getElementById("select");
  select.innerHTML = ""; // clear old options

  checkers.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value.toUpperCase();
    select.appendChild(option);
  });

  // Show first value by default
  document.getElementById("output-text").textContent = "You selected: " + select.value;

  // Update output-text when user changes selection
  select.addEventListener("change", () => {
    document.getElementById("output-text").textContent = "You selected: " + select.value;
  });
}
