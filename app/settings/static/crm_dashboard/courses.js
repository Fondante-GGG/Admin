(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function closeAllDropdowns() {
    qsa(".crm-dd").forEach(dd => dd.classList.remove("is-open"));
  }

  document.addEventListener("click", (e) => {
    const toggle = e.target.closest("[data-dd-toggle]");
    if (toggle) {
      const dd = toggle.closest(".crm-dd");
      if (!dd) return;
      const isOpen = dd.classList.contains("is-open");
      closeAllDropdowns();
      if (!isOpen) dd.classList.add("is-open");
      e.preventDefault();
      return;
    }

    const scrollBtn = e.target.closest("[data-scroll-to]");
    if (scrollBtn) {
      const target = scrollBtn.getAttribute("data-scroll-to");
      const el = target ? qs(target) : null;
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      closeAllDropdowns();
      e.preventDefault();
      return;
    }

    const actionEl = e.target.closest("[data-action]");
    if (actionEl) {
      const action = actionEl.getAttribute("data-action");
      const toolbar = qs(".crm-toolbar");
      const csvUrl = toolbar ? toolbar.getAttribute("data-students-csv-url") : null;

      if (action === "export" && csvUrl) {
        window.location.href = csvUrl;
        closeAllDropdowns();
        e.preventDefault();
        return;
      }

      if (action === "reg-link") {
        const url = window.location.origin + "/register/";
        navigator.clipboard?.writeText(url);
        alert("Ссылка скопирована: " + url);
        closeAllDropdowns();
        e.preventDefault();
        return;
      }

      if (action === "add-student") {
        const addBtn = qs("#enrollment-inline .add-row a");
        if (addBtn) addBtn.click();
        const inline = qs("#enrollment-inline");
        if (inline) inline.scrollIntoView({ behavior: "smooth", block: "start" });
        closeAllDropdowns();
        e.preventDefault();
        return;
      }

      if (action === "invite" || action === "notify" || action === "notify-debtors" || action === "landing") {
        alert("Пока заглушка. Скажи, что именно должно происходить — сделаю полностью.");
        closeAllDropdowns();
        e.preventDefault();
        return;
      }
    }

    if (!e.target.closest(".crm-dd")) closeAllDropdowns();
  });

  // mark inlines for scroll anchors
  document.addEventListener("DOMContentLoaded", () => {
    const enrollInline = qsa(".inline-group").find(g => (g.id || "").includes("enrollment") || g.querySelector("input[name$='-tuition_amount']"));
    if (enrollInline && !enrollInline.id) enrollInline.id = "enrollment-inline";
  });
})();

