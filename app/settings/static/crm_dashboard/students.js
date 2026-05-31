(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  /** Click target may be a Text node; only Elements have .closest */
  function clickEl(e) {
    const t = e.target;
    if (!t) return null;
    return t.nodeType === 1 ? t : t.parentElement;
  }

  function initStudentDrawer() {
    const drawer = qs("[data-st-drawer]");
    const panel = drawer ? qs(".crm-drawer__panel", drawer) : null;
    const tpl = drawer ? drawer.getAttribute("data-drawer-url-template") : null;
    if (!drawer || !panel || !tpl) return;

    const courseId = drawer.getAttribute("data-drawer-course");

    const payFilters = qs("[data-st-pay-filters]");
    const togglePayFilters = qs("[data-st-toggle-pay-filters]");
    togglePayFilters?.addEventListener("click", () => {
      payFilters?.classList.toggle("is-hidden");
    });

    function urlForStudentId(id) {
      let url = tpl.replace(/\/\d+\/drawer\/?/, `/${id}/drawer/`);
      if (courseId) {
        url += (url.includes("?") ? "&" : "?") + "course=" + encodeURIComponent(courseId);
      }
      return url;
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
      const el = clickEl(e);
      if (!el) return;

      const closeBtn = el.closest("[data-st-close]");
      if (closeBtn) {
        close();
        return;
      }

      const row = el.closest("tr[data-student-row]");
      if (row && !el.closest("input, button, a, label")) {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        const sid = row.getAttribute("data-student-id");
        if (sid) {
          e.preventDefault();
          loadStudent(sid);
          return;
        }
      }

      // click on student id link (#123) or name link
      const a = el.closest("a");
      if (!a) return;
      if (a.hasAttribute("data-st-nodrawer")) return;
      if (e.button !== 0) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const href = a.getAttribute("href") || "";
      // drawer pager links (?p=2)
      if (a.classList.contains("crm-pg")) {
        e.preventDefault();
        const u = new URL(href, window.location.origin);
        // keep current student id in drawer url
        const current = panel.querySelector("a[href*='/admin-men/settings/student/']")?.getAttribute("href") || "";
        const m2 =
          current.match(/student\/(\d+)\//) ||
          current.match(/\/(\d+)\/change\/?/) ||
          current.match(/^(\d+)\/change\/?/);
        if (!m2) return;
        const id = m2[1];
        const drawerUrl = new URL(urlForStudentId(id), window.location.origin);
        drawerUrl.search = u.search;
        if (courseId && !drawerUrl.searchParams.has("course")) {
          drawerUrl.searchParams.set("course", courseId);
        }
        loadHref(drawerUrl.toString());
        return;
      }
      if (a.classList.contains("crm-student-link")) {
        e.preventDefault();
        const sid = a.getAttribute("data-student-id");
        if (sid) loadStudent(sid);
        return;
      }
      // href may be absolute or relative (e.g. "166/change/" or "/admin-men/.../student/166/change/")
      const m =
        href.match(/student\/(\d+)\//) ||
        href.match(/\/(\d+)\/change\/?/) ||
        href.match(/^(\d+)\/change\/?/);
      if (!m) return;

      e.preventDefault();
      const id = m[1];
      loadStudent(id);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !drawer.classList.contains("is-hidden")) close();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initStudentDrawer);
  } else {
    initStudentDrawer();
  }
})();
