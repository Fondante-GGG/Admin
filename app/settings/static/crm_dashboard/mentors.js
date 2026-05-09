(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  var modal = qs("#crm-mentor-modal");
  if (!modal) return;

  var form = qs("#crm-mentor-create-form");
  var openBtn = qs("[data-mentor-open-modal]");
  var closeEls = document.querySelectorAll("[data-mentor-close-modal]");
  var fileErr = qs("[data-mentor-file-error]");
  var fileInput = form ? form.querySelector('input[name="contract_file"]') : null;
  var maxBytes = fileInput ? parseInt(fileInput.getAttribute("data-max-bytes") || "0", 10) : 0;

  function openModal() {
    modal.hidden = false;
    modal.classList.remove("is-hidden");
    document.body.classList.add("crm-mentor-modal-open");
    if (fileErr) {
      fileErr.hidden = true;
      fileErr.textContent = "";
    }
    var first = modal.querySelector("input[name='first_name']");
    if (first) first.focus();
  }

  function closeModal() {
    modal.classList.add("is-hidden");
    modal.hidden = true;
    document.body.classList.remove("crm-mentor-modal-open");
  }

  function showFileError(msg) {
    if (!fileErr) {
      window.alert(msg);
      return;
    }
    fileErr.textContent = msg;
    fileErr.hidden = false;
  }

  openBtn?.addEventListener("click", function (e) {
    e.preventDefault();
    openModal();
  });

  closeEls.forEach(function (el) {
    el.addEventListener("click", function () {
      closeModal();
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.classList.contains("is-hidden")) {
      closeModal();
    }
  });

  fileInput?.addEventListener("change", function () {
    if (!fileErr) return;
    fileErr.hidden = true;
    fileErr.textContent = "";
    var f = fileInput.files && fileInput.files[0];
    if (!f) return;
    if (maxBytes > 0 && f.size > maxBytes) {
      showFileError("Файл контракта не должен превышать 5 МБ.");
      fileInput.value = "";
      return;
    }
    var name = (f.name || "").toLowerCase();
    if (name && !name.endsWith(".pdf")) {
      showFileError("Разрешён только формат PDF.");
      fileInput.value = "";
    }
  });

  form?.addEventListener("submit", function (e) {
    var f = fileInput && fileInput.files && fileInput.files[0];
    if (f && maxBytes > 0 && f.size > maxBytes) {
      e.preventDefault();
      showFileError("Файл контракта не должен превышать 5 МБ.");
      return;
    }
    if (f) {
      var name = (f.name || "").toLowerCase();
      if (name && !name.endsWith(".pdf")) {
        e.preventDefault();
        showFileError("Разрешён только формат PDF.");
      }
    }
  });
})();
