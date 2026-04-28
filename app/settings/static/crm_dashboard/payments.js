(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const toolbar = qs("[data-pay-toolbar]");
  if (!toolbar) return;

  function setParams(updates) {
    const url = new URL(window.location.href);
    Object.entries(updates).forEach(([k, v]) => {
      if (!v) url.searchParams.delete(k);
      else url.searchParams.set(k, v);
    });
    // reset pagination on filter change
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

  qs("[data-pay-clear]", toolbar)?.addEventListener("click", () => {
    qsa("[data-pay]", toolbar).forEach((el) => (el.value = ""));
    setParams(collect());
  });

  // Enter in pay_id triggers apply
  qsa("[data-pay='pay_id']", toolbar).forEach((el) => {
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        setParams(collect());
      }
    });
  });
})();

