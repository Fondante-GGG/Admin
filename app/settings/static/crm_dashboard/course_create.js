(function () {
  function qsa(selector, root) {
    return Array.from((root || document).querySelectorAll(selector));
  }

  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }

  function closeDropdowns() {
    qsa("[data-course-create-dd]").forEach(function (dd) {
      dd.classList.remove("is-open");
    });
  }

  function closeModal(root) {
    var modal = qs("[data-course-create-modal]", root);
    if (!modal) return;
    modal.classList.add("is-hidden");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("crm-course-create-open");
  }

  function closeModals() {
    qsa("[data-course-create-root]").forEach(closeModal);
  }

  function updateColor(root) {
    var select = qs("[data-course-create-color]", root);
    var preview = qs("[data-course-create-color-preview]", root);
    if (!select || !preview) return;
    preview.style.backgroundColor = select.value || "#8ed99a";
  }

  function openModal(root, trigger) {
    var modal = qs("[data-course-create-modal]", root);
    var form = qs("form", modal);
    if (!modal || !form) return;

    form.reset();
    var variant = trigger.getAttribute("data-course-variant") || "ordinary";
    var label = trigger.getAttribute("data-course-label") || "Обычный курс";
    var variantInput = qs("[data-course-create-variant]", root);
    var title = qs("[data-course-create-title]", root);

    if (variantInput) variantInput.value = variant;
    if (title) title.textContent = label;
    updateColor(root);

    modal.classList.remove("is-hidden");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("crm-course-create-open");

    window.setTimeout(function () {
      var focusTarget = qs("[data-course-create-focus]", root);
      if (focusTarget) focusTarget.focus();
    }, 40);
  }

  document.addEventListener("click", function (event) {
    var target = event.target;
    var el = target && target.nodeType === 1 ? target : target && target.parentElement;
    if (!el) return;

    var toggle = el.closest("[data-course-create-toggle]");
    if (toggle) {
      event.preventDefault();
      var dd = toggle.closest("[data-course-create-dd]");
      var isOpen = dd && dd.classList.contains("is-open");
      closeDropdowns();
      if (dd && !isOpen) dd.classList.add("is-open");
      return;
    }

    var openButton = el.closest("[data-course-create-open]");
    if (openButton) {
      event.preventDefault();
      var root = openButton.closest("[data-course-create-root]");
      closeDropdowns();
      if (root) openModal(root, openButton);
      return;
    }

    var closeButton = el.closest("[data-course-create-close]");
    if (closeButton) {
      event.preventDefault();
      var closeRoot = closeButton.closest("[data-course-create-root]");
      if (closeRoot) closeModal(closeRoot);
      return;
    }

    if (!el.closest("[data-course-create-dd]")) {
      closeDropdowns();
    }
  });

  document.addEventListener("change", function (event) {
    var target = event.target;
    if (!target || !target.matches("[data-course-create-color]")) return;
    var root = target.closest("[data-course-create-root]");
    if (root) updateColor(root);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    closeDropdowns();
    closeModals();
  });

  document.addEventListener("DOMContentLoaded", function () {
    qsa("[data-course-create-root]").forEach(updateColor);
  });
})();
