(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const toolbar = qs("[data-acc-toolbar]");

  const label = qs("[data-acc-label]", toolbar);
  const startMonth = (toolbar.getAttribute("data-acc-month") || "").trim();

  function parseMonth(m) {
    const [y, mo] = m.split("-").map((x) => parseInt(x, 10));
    if (!y || !mo) return null;
    return { y, mo };
  }

  function fmtLabel(y, mo) {
    const names = [
      "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ];
    return `${names[mo - 1] || ""} ${y}`;
  }

  function setMonth(y, mo) {
    if (mo < 1) { y -= 1; mo = 12; }
    if (mo > 12) { y += 1; mo = 1; }
    const mm = String(mo).padStart(2, "0");

    if (label) label.textContent = fmtLabel(y, mo);

    const url = new URL(window.location.href);
    url.searchParams.set("m", `${y}-${mm}`);
    url.searchParams.delete("p");
    window.location.href = url.pathname + "?" + url.searchParams.toString();
  }

  const cur = parseMonth(startMonth) || parseMonth(new Date().toISOString().slice(0, 7));
  if (cur && label) label.textContent = fmtLabel(cur.y, cur.mo);

  qs("[data-acc-prev]", toolbar)?.addEventListener("click", () => setMonth(cur.y, cur.mo - 1));
  qs("[data-acc-next]", toolbar)?.addEventListener("click", () => setMonth(cur.y, cur.mo + 1));

  const filterRoot = qs("[data-acc-filter]");
  const qInput = qs("[data-acc-q]", filterRoot);
  const applyBtn = qs("[data-acc-apply]", filterRoot);

  function applyFilters() {
    const url = new URL(window.location.href);
    const q = (qInput?.value || "").trim();
    if (!q) url.searchParams.delete("q");
    else url.searchParams.set("q", q);
    url.searchParams.delete("p");
    window.location.href = url.pathname + "?" + url.searchParams.toString();
  }

  applyBtn?.addEventListener("click", applyFilters);
  qInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      applyFilters();
    }
  });

  // Modal create (income/expense/transfer)
  const modal = qs("[data-acc-modal]");
  if (!modal) return;
  const closeBtns = qsa("[data-acc-close]", modal);
  const titleEl = qs("[data-acc-modal-title]", modal);
  const form = qs("[data-acc-form]", modal);
  const entryGrid = qs("[data-acc-form-entry]", modal);
  const transferGrid = qs("[data-acc-form-transfer]", modal);

  const selAccount = qs("[data-acc-account]", modal);
  const selFrom = qs("[data-acc-from]", modal);
  const selTo = qs("[data-acc-to]", modal);
  const selProject = qsa("[data-acc-project]", modal);
  const selCategory = qsa("[data-acc-category]", modal);

  let mode = "income";
  let metaLoaded = false;

  function todayLocalValue() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function setSelectOptions(select, items, includeEmpty) {
    if (!select) return;
    select.innerHTML = "";
    if (includeEmpty) {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "---------";
      select.appendChild(o);
    }
    (items || []).forEach((it) => {
      const o = document.createElement("option");
      o.value = String(it.id);
      o.textContent = it.title;
      select.appendChild(o);
    });
  }

  async function ensureMeta() {
    if (metaLoaded) return;
    try {
      const resp = await fetch("/admin/accounting/meta/", { credentials: "same-origin" });
      const data = await resp.json();
      setSelectOptions(selAccount, data.accounts, false);
      setSelectOptions(selFrom, data.accounts, false);
      setSelectOptions(selTo, data.accounts, false);
      selProject.forEach((s) => setSelectOptions(s, data.projects, true));
      selCategory.forEach((s) => setSelectOptions(s, data.categories, true));
      metaLoaded = true;
    } catch (e) {
      // allow opening modal even if meta failed
      setSelectOptions(selAccount, [], false);
      setSelectOptions(selFrom, [], false);
      setSelectOptions(selTo, [], false);
      selProject.forEach((s) => setSelectOptions(s, [], true));
      selCategory.forEach((s) => setSelectOptions(s, [], true));
      metaLoaded = true;
    }
  }

  function openModal(newMode) {
    mode = newMode;
    modal.hidden = false;
    document.body.style.overflow = "hidden";

    const dtInputs = qsa("input[name='operated_at']", modal);
    dtInputs.forEach((i) => { i.value = todayLocalValue(); });

    function setGridDisabled(root, disabled) {
      if (!root) return;
      qsa("input, select, textarea, button", root).forEach((el) => {
        // keep the submit button active (it's outside grids anyway)
        el.disabled = !!disabled;
      });
    }

    if (mode === "transfer") {
      titleEl.textContent = "Перевод";
      entryGrid.hidden = true;
      transferGrid.hidden = false;
      setGridDisabled(entryGrid, true);
      setGridDisabled(transferGrid, false);
    } else if (mode === "expense") {
      titleEl.textContent = "Расход";
      entryGrid.hidden = false;
      transferGrid.hidden = true;
      setGridDisabled(entryGrid, false);
      setGridDisabled(transferGrid, true);
    } else {
      titleEl.textContent = "Приход";
      entryGrid.hidden = false;
      transferGrid.hidden = true;
      setGridDisabled(entryGrid, false);
      setGridDisabled(transferGrid, true);
    }
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  closeBtns.forEach((b) => b.addEventListener("click", closeModal));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && !modal.hidden) closeModal();
  });

  // Bind globally (admin layouts can re-render blocks)
  document.addEventListener("click", async (e) => {
    const btn = e.target?.closest?.("[data-acc-open]");
    if (!btn) return;
    e.preventDefault();
    await ensureMeta();
    openModal(btn.getAttribute("data-acc-open"));
  });

  function formToBody(formEl) {
    const fd = new FormData(formEl);
    // Only keep relevant fields for current mode
    if (mode === "transfer") {
      fd.delete("account");
      fd.set("operated_at", fd.get("operated_at") || "");
      return fd;
    }
    fd.delete("from_account");
    fd.delete("to_account");
    fd.set("entry_type", mode === "expense" ? "expense" : "income");
    return fd;
  }

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = mode === "transfer" ? "/admin/accounting/transfer/create/" : "/admin/accounting/entry/create/";
    const body = formToBody(form);
    function getCookie(name) {
      const m = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
      return m ? decodeURIComponent(m[2]) : "";
    }
    const csrftoken = getCookie("csrftoken");
    const resp = await fetch(url, {
      method: "POST",
      body,
      credentials: "same-origin",
      headers: csrftoken ? { "X-CSRFToken": csrftoken } : {},
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) {
      alert(data.error || "Ошибка сохранения");
      return;
    }
    closeModal();
    window.location.reload();
  });
})();
