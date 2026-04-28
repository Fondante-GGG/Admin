(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  const toolbar = qs("[data-debt-toolbar]");
  if (!toolbar) return;

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
    qsa("[data-debt]", toolbar).forEach((el) => {
      const key = el.getAttribute("data-debt");
      data[key] = (el.value || "").trim();
    });
    return data;
  }

  qs("[data-debt-apply]", toolbar)?.addEventListener("click", () => setParams(collect()));
  qs("[data-debt-clear]", toolbar)?.addEventListener("click", () => {
    qsa("[data-debt]", toolbar).forEach((el) => (el.value = ""));
    setParams(collect());
  });

  qsa("[data-debt='q']", toolbar).forEach((el) => {
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        setParams(collect());
      }
    });
  });
})();

