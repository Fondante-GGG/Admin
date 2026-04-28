(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const drawer = qs("[data-st-drawer]");
  const panel = drawer ? qs(".crm-drawer__panel", drawer) : null;
  const tpl = drawer ? drawer.getAttribute("data-drawer-url-template") : null;
  if (!drawer || !panel || !tpl) return;

  const payFilters = qs("[data-st-pay-filters]");
  const togglePayFilters = qs("[data-st-toggle-pay-filters]");
  togglePayFilters?.addEventListener("click", () => {
    payFilters?.classList.toggle("is-hidden");
  });

  function urlForStudentId(id) {
    // template is .../students/1/drawer/
    return tpl.replace("/1/drawer/", `/${id}/drawer/`);
  }

  function open() {
    drawer.classList.remove("is-hidden");
    document.body.classList.add("crm-drawer-open");
  }

  function close() {
    drawer.classList.add("is-hidden");
    document.body.classList.remove("crm-drawer-open");
  }

  async function loadStudent(id) {
    panel.innerHTML = '<div class="crm-drawer__loading">Загрузка…</div>';
    open();
    const res = await fetch(urlForStudentId(id), { credentials: "same-origin" });
    if (!res.ok) {
      panel.innerHTML = "<div class='crm-drawer__loading'>Ошибка загрузки</div>";
      return;
    }
    panel.innerHTML = await res.text();
  }

  async function loadHref(href) {
    panel.innerHTML = '<div class="crm-drawer__loading">Загрузка…</div>';
    open();
    const res = await fetch(href, { credentials: "same-origin" });
    if (!res.ok) {
      panel.innerHTML = "<div class='crm-drawer__loading'>Ошибка загрузки</div>";
      return;
    }
    panel.innerHTML = await res.text();
  }

  document.addEventListener("click", (e) => {
    const closeBtn = e.target.closest("[data-st-close]");
    if (closeBtn) {
      close();
      return;
    }

    // click on student id link (#123) or name link
    const a = e.target.closest("a");
    if (!a) return;
    if (e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const href = a.getAttribute("href") || "";
    // drawer pager links (?p=2)
    if (a.classList.contains("crm-pg")) {
      e.preventDefault();
      const u = new URL(href, window.location.origin);
      // keep current student id in drawer url
      const current = panel.querySelector("a[href*='/admin/settings/student/']")?.getAttribute("href") || "";
      const m2 = current.match(/student\\/(\\d+)\\//) || current.match(/\\/(\\d+)\\/change\\/?/);
      if (!m2) return;
      const id = m2[1];
      const drawerUrl = new URL(urlForStudentId(id), window.location.origin);
      drawerUrl.search = u.search;
      loadHref(drawerUrl.toString());
      return;
    }
    // href may be absolute or relative (e.g. "166/change/")
    const m = href.match(/student\\/(\\d+)\\//) || href.match(/\\/(\\d+)\\/change\\/?/);
    if (!m) return;

    e.preventDefault();
    const id = m[1];
    loadStudent(id);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !drawer.classList.contains("is-hidden")) close();
  });
})();
