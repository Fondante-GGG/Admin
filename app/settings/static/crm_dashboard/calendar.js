(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const el = qs("#crmCalendar");
  if (!el) return;

  const eventsUrl = el.getAttribute("data-events-url");
  const createUrl = el.getAttribute("data-create-url");

  const filtersWrap = qs("[data-cal-filters]");
  const btnToggleFilters = qs("[data-cal-toggle-filters]");
  const btnApply = qs("[data-cal-apply]");
  const btnClear = qs("[data-cal-clear]");

  const btnPrev = qs("[data-cal-prev]");
  const btnNext = qs("[data-cal-next]");
  const titleEl = qs("[data-cal-title]");
  const viewBtns = qsa("[data-cal-view]");

  const modal = qs("[data-cal-modal]");
  const openCreate = qs("[data-cal-open-create]");
  const form = qs("[data-cal-form]");

  function mapTextToId(key, text) {
    const t = (text || "").trim().toLowerCase();
    if (!t) return "";
    if (key === "course") {
      const opt = qsa("#calCourses option").find((o) => (o.value || "").trim().toLowerCase() === t);
      if (!opt) return "";
      // try to find matching select option by text (server uses ids)
      // We'll send course_title too; backend accepts both.
      return opt.value;
    }
    return text;
  }

  function currentParams() {
    const params = new URLSearchParams(window.location.search);
    qsa("[data-cal-filter-text]").forEach((inp) => {
      const k = inp.getAttribute("data-cal-filter-text");
      const v = (inp.value || "").trim();
      if (v) params.set(k, v);
      else params.delete(k);
    });
    return params;
  }

  function loadEvents(info, success, failure) {
    const params = currentParams();
    fetch(eventsUrl + "?" + params.toString(), { credentials: "same-origin" })
      .then((r) => r.json())
      .then(success)
      .catch(failure);
  }

  const calendar = new FullCalendar.Calendar(el, {
    initialView: "dayGridMonth",
    height: "auto",
    headerToolbar: false,
    locale: "ru",
    firstDay: 1,
    nowIndicator: true,
    events: loadEvents,
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
  });

  calendar.render();

  function updateTitle() {
    if (!titleEl) return;
    const d = calendar.getDate();
    const fmt = new Intl.DateTimeFormat("ru", { month: "long", year: "numeric" });
    const t = fmt.format(d);
    titleEl.textContent = t.charAt(0).toUpperCase() + t.slice(1);
  }

  function setActiveView(viewName) {
    viewBtns.forEach((b) => b.classList.toggle("is-active", b.getAttribute("data-cal-view") === viewName));
  }

  updateTitle();
  setActiveView(calendar.view.type);

  btnPrev?.addEventListener("click", () => {
    calendar.prev();
    updateTitle();
  });

  btnNext?.addEventListener("click", () => {
    calendar.next();
    updateTitle();
  });

  viewBtns.forEach((b) => {
    b.addEventListener("click", () => {
      const v = b.getAttribute("data-cal-view");
      if (!v) return;
      calendar.changeView(v);
      setActiveView(v);
      updateTitle();
    });
  });

  function openModal() { modal?.classList.remove("is-hidden"); }
  function closeModal() { modal?.classList.add("is-hidden"); }

  btnToggleFilters?.addEventListener("click", () => {
    filtersWrap?.classList.toggle("is-hidden");
  });

  openCreate?.addEventListener("click", () => {
    openModal();
  });

  qsa("[data-cal-close]").forEach((x) => x.addEventListener("click", closeModal));

  btnApply?.addEventListener("click", () => {
    calendar.refetchEvents();
  });

  btnClear?.addEventListener("click", () => {
    qsa("[data-cal-filter-text]").forEach((s) => (s.value = ""));
    calendar.refetchEvents();
  });

  // hydrate selects from query
  const urlParams = new URLSearchParams(window.location.search);
  qsa("[data-cal-filter-text]").forEach((sel) => {
    const k = sel.getAttribute("data-cal-filter-text");
    if (urlParams.has(k)) sel.value = urlParams.get(k);
  });

  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const date = fd.get("date");
    const startTime = fd.get("start_time");
    const endTime = fd.get("end_time");
    const startAt = date && startTime ? `${date}T${startTime}` : "";
    const endAt = date && endTime ? `${date}T${endTime}` : "";

    const post = new FormData();
    post.set("title", fd.get("title") || "");
    post.set("course", fd.get("course") || "");
    post.set("location", fd.get("location") || "");
    post.set("online_link", fd.get("online_link") || "");
    post.set("description", fd.get("description") || "");
    post.set("start_at", startAt);
    post.set("end_at", endAt);

    const csrf = qs("input[name=csrfmiddlewaretoken]", form)?.value;
    fetch(createUrl, {
      method: "POST",
      body: post,
      headers: csrf ? { "X-CSRFToken": csrf } : {},
      credentials: "same-origin",
    })
      .then((r) => r.json().then((j) => ({ ok: r.ok, j })))
      .then(({ ok, j }) => {
        if (!ok || !j.ok) throw new Error(j.error || "Ошибка");
        closeModal();
        form.reset();
        calendar.refetchEvents();
      })
      .catch((err) => {
        alert(err.message || "Ошибка сохранения");
      });
  });
})();
