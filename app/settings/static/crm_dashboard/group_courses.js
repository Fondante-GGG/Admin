(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function setParam(url, key, value) {
    const u = new URL(url, window.location.origin);
    if (!value) u.searchParams.delete(key);
    else u.searchParams.set(key, value);
    return u.pathname + "?" + u.searchParams.toString();
  }

  function closeMenus() {
    qsa(".crm-filter-dd").forEach(x => x.classList.remove("is-open"));
  }

  document.addEventListener("click", (e) => {
    const toggle = e.target.closest("[data-filter-toggle]");
    if (toggle) {
      const dd = toggle.closest(".crm-filter-dd");
      if (!dd) return;
      const open = dd.classList.contains("is-open");
      closeMenus();
      if (!open) dd.classList.add("is-open");
      e.preventDefault();
      return;
    }

    const setView = e.target.closest("[data-set-view]");
    if (setView) {
      const view = setView.getAttribute("data-set-view");
      window.location.href = setParam(window.location.href, "view", view);
      e.preventDefault();
      return;
    }

    const setItem = e.target.closest("[data-set-param]");
    if (setItem) {
      const key = setItem.getAttribute("data-set-param");
      const value = setItem.getAttribute("data-value") || "";
      window.location.href = setParam(window.location.href, key, value);
      e.preventDefault();
      return;
    }

    if (!e.target.closest(".crm-filter-dd")) closeMenus();
  });
})();

