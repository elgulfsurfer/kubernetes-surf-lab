// Sliders — update displayed value in real time
document.querySelectorAll("input[type='range'][data-output]").forEach(function(slider) {
  var output = document.getElementById(slider.dataset.output);
  if (output) {
    slider.addEventListener("input", function() {
      output.textContent = slider.value;
    });
  }
});

// Char counter for textareas
document.querySelectorAll("textarea[data-counter]").forEach(function(ta) {
  var counter = document.getElementById(ta.dataset.counter);
  if (counter) {
    ta.addEventListener("input", function() {
      counter.textContent = ta.value.length + "/200";
    });
  }
});

// Clickable table rows
document.querySelectorAll("tr.clickable[data-href]").forEach(function(row) {
  row.addEventListener("click", function() {
    window.location = row.dataset.href;
  });
});

// Delete confirm button — disable until user types "delete"
document.querySelectorAll(".delete-form").forEach(function(form) {
  var input = form.querySelector("input[name='confirm']");
  var btn   = form.querySelector("[data-delete-btn]");
  if (!input || !btn) return;

  btn.disabled = true;
  input.addEventListener("input", function() {
    btn.disabled = input.value !== "delete";
  });
});
