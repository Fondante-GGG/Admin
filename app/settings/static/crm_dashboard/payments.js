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
    if (!e.target.closest(".crm-pay-actions-dd")) {
      closeAllPayMenus();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAllPayMenus();
  });

  document.addEventListener(
    "click",
    (e) => {
      const item = e.target.closest("[data-pay-action]");
      if (!item) return;
      e.preventDefault();
    },
    true
  );
})();
