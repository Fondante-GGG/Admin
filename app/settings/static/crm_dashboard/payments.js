(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }
  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  const toolbar = qs("[data-pay-toolbar]");
  if (toolbar) {
    function setParams(updates) {
      const url = new URL(window.location.href);
      Object.entries(updates).forEach(([k, v]) => {
        if (!v) url.searchParams.delete(k);
        else url.searchParams.set(k, v);
      });
      url.searchParams.delete("p");
      window.location.href = url.pathname + "?" + url.searchParams.toString();
    }

    function collect() {
      const data = {};
      qsa("[data-pay]", toolbar).forEach((el) => {
        const key = el.getAttribute("data-pay");
        data[key] = (el.value || "").trim();
      });
      return data;
    }

    qs("[data-pay-apply]", toolbar)?.addEventListener("click", () => {
      setParams(collect());
    });

    qsa("[data-pay='pay_id']", toolbar).forEach((el) => {
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          setParams(collect());
        }
      });
    });
  }

  function closeAllPayMenus() {
    qsa("[data-pay-dd-toggle]").forEach((btn) => {
      btn.setAttribute("aria-expanded", "false");
      const wrap = btn.closest(".crm-pay-actions-dd");
      const menu = wrap && wrap.querySelector(".crm-pay-actions-menu");
      if (menu) menu.hidden = true;
    });
  }

  function openModal(id) {
    const modal = qs(id);
    if (modal) {
      modal.hidden = false;
      document.body.style.overflow = "hidden";
    }
  }

  function closeAllModals() {
    qsa(".crm-modal-overlay").forEach((m) => {
      m.hidden = true;
    });
    document.body.style.overflow = "";
  }

  function getCsrfToken() {
    const input = qs('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
  }

  document.addEventListener("click", (e) => {
    const toggle = e.target.closest("[data-pay-dd-toggle]");
    if (toggle) {
      e.preventDefault();
      e.stopPropagation();
      const wrap = toggle.closest(".crm-pay-actions-dd");
      const menu = wrap && wrap.querySelector(".crm-pay-actions-menu");
      if (!menu) return;
      const willOpen = menu.hidden;
      closeAllPayMenus();
      if (willOpen) {
        menu.hidden = false;
        toggle.setAttribute("aria-expanded", "true");
      }
      return;
    }

    const actionBtn = e.target.closest("[data-pay-action]");
    if (actionBtn) {
      e.preventDefault();
      e.stopPropagation();
      const action = actionBtn.getAttribute("data-pay-action");
      const payId = actionBtn.getAttribute("data-pay-id");
      closeAllPayMenus();

      if (action === "receipt") {
        const form = document.createElement("form");
        form.method = "post";
        form.action = window.location.pathname;
        form.style.display = "none";
        const csrf = document.createElement("input");
        csrf.name = "csrfmiddlewaretoken";
        csrf.value = getCsrfToken();
        const actionInput = document.createElement("input");
        actionInput.name = "action";
        actionInput.value = "receipt";
        const idInput = document.createElement("input");
        idInput.name = "pay_id";
        idInput.value = payId;
        form.append(csrf, actionInput, idInput);
        document.body.appendChild(form);
        form.submit();
        return;
      }

      if (action === "edit") {
        qs("#edit-pay-id").value = payId;
        openModal("#crm-modal-edit");
        return;
      }

      if (action === "void") {
        qs("#void-pay-id").value = payId;
        openModal("#crm-modal-void");
        return;
      }

      if (action === "attach") {
        qs("#attach-pay-id").value = payId;
        qs("#attach-file").value = "";
        qs("#attach-file-name").textContent = "Файл не выбран";
        qs("#attach-filename").value = "";
        openModal("#crm-modal-attach");
        return;
      }
    }

    if (!e.target.closest(".crm-pay-actions-dd")) {
      closeAllPayMenus();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeAllPayMenus();
      closeAllModals();
    }
  });

  document.addEventListener("click", (e) => {
    const closeBtn = e.target.closest("[data-modal-close]");
    if (closeBtn) {
      e.preventDefault();
      closeAllModals();
      return;
    }

    const overlay = e.target.closest(".crm-modal-overlay");
    if (overlay && e.target === overlay) {
      closeAllModals();
      return;
    }

    const submitBtn = e.target.closest("[data-modal-submit]");
    if (submitBtn) {
      e.preventDefault();
      const formId = submitBtn.getAttribute("data-modal-submit");
      const form = qs("#" + formId);
      if (!form) return;

      if (formId === "crm-form-attach") {
        const fileInput = qs("#attach-file");
        if (!fileInput.files.length) {
          alert("Выберите файл");
          return;
        }
        const file = fileInput.files[0];
        if (file.size > 10 * 1024 * 1024) {
          alert("Файл слишком большой. Максимальный размер: 10 МБ");
          return;
        }
        form.submit();
        return;
      }

      form.submit();
    }
  });

  const attachFileInput = qs("#attach-file");
  if (attachFileInput) {
    attachFileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      const nameEl = qs("#attach-file-name");
      const filenameEl = qs("#attach-filename");
      if (file) {
        nameEl.textContent = file.name;
        filenameEl.value = file.name;
      } else {
        nameEl.textContent = "Файл не выбран";
        filenameEl.value = "";
      }
    });
  }
})();
