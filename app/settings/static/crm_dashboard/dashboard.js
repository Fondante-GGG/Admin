function parseDashboardData() {
  const node = document.getElementById("dashboard-series");
  if (!node) return null;
  try {
    return { series: JSON.parse(node.textContent || "{}") };
  } catch {
    return null;
  }
}

function getNiceMax(maxVal) {
  if (maxVal <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(maxVal)));
  const n = maxVal / pow;
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10;
  return nice * pow;
}

function drawAxes(ctx, w, h, pad, maxY, labels) {
  ctx.strokeStyle = "rgba(16,24,40,0.10)";
  ctx.lineWidth = 1;

  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, h - pad);
  ctx.lineTo(w - pad, h - pad);
  ctx.stroke();

  const steps = 4;
  ctx.fillStyle = "rgba(16,24,40,0.45)";
  ctx.font = "11px system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif";
  for (let i = 0; i <= steps; i++) {
    const y = pad + ((h - 2 * pad) * i) / steps;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(w - pad, y);
    ctx.stroke();
    const v = Math.round(maxY * (1 - i / steps));
    ctx.fillText(String(v), 6, y + 4);
  }

  const showEvery = Math.ceil(labels.length / 6);
  for (let i = 0; i < labels.length; i += showEvery) {
    const x = pad + ((w - 2 * pad) * i) / Math.max(1, labels.length - 1);
    ctx.save();
    ctx.translate(x, h - pad + 14);
    ctx.rotate(-Math.PI / 6);
    ctx.fillText(labels[i], 0, 0);
    ctx.restore();
  }
}

function drawBar(ctx, w, h, pad, labels, values, color, offset = 0, seriesCount = 1, options = {}) {
  const maxVal = Math.max(...values, 1);
  const maxY = getNiceMax(maxVal);
  drawAxes(ctx, w, h, pad, maxY, labels);

  const plotW = w - 2 * pad;
  const plotH = h - 2 * pad;
  const barW = plotW / values.length;
  const innerW = barW * 0.78;
  const groupW = innerW / seriesCount;

  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    const x0 = pad + i * barW + (barW - innerW) / 2 + offset * groupW;
    const barH = (v / maxY) * plotH;
    const y0 = h - pad - barH;
    const r = 6;
    const bw = Math.max(2, groupW - 2);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x0, y0 + r);
    ctx.arcTo(x0, y0, x0 + r, y0, r);
    ctx.arcTo(x0 + bw, y0, x0 + bw, y0 + r, r);
    ctx.lineTo(x0 + bw, h - pad);
    ctx.lineTo(x0, h - pad);
    ctx.closePath();
    ctx.fill();
    if (options.stroke) {
      ctx.strokeStyle = options.stroke;
      ctx.lineWidth = options.lineWidth || 1;
      ctx.stroke();
    }
  }
}

function drawDiverging(ctx, w, h, pad, labels, income, expense) {
  const maxMag = getNiceMax(Math.max(Math.max(...income, 1), Math.max(...expense, 1)));
  const plotW = w - 2 * pad;
  const plotH = h - 2 * pad;
  const midY = pad + plotH / 2;
  const halfH = plotH / 2 - 6;

  ctx.strokeStyle = "rgba(16,24,40,0.12)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, h - pad);
  ctx.lineTo(w - pad, h - pad);
  ctx.lineTo(w - pad, pad);
  ctx.closePath();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(pad, midY);
  ctx.lineTo(w - pad, midY);
  ctx.stroke();

  ctx.fillStyle = "rgba(16,24,40,0.45)";
  ctx.font = "11px system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif";
  ctx.fillText(String(Math.round(maxMag)), 6, pad + 10);
  ctx.fillText("0", 6, midY + 4);
  ctx.fillText("-" + String(Math.round(maxMag)), 6, h - pad - 4);

  const n = income.length;
  const barW = plotW / Math.max(n, 1);
  const inner = Math.max(4, barW * 0.32);

  for (let i = 0; i < n; i++) {
    const x0 = pad + i * barW + (barW - inner) / 2;
    const hIn = (income[i] / maxMag) * halfH;
    const hEx = (expense[i] / maxMag) * halfH;
    ctx.fillStyle = "#6c5ce7";
    ctx.fillRect(x0, midY - hIn, inner, hIn);
    ctx.fillStyle = "#f5a25d";
    ctx.fillRect(x0, midY, inner, hEx);
  }

  const showEvery = Math.ceil(labels.length / 6);
  for (let i = 0; i < labels.length; i += showEvery) {
    const x = pad + (plotW * i) / Math.max(1, labels.length - 1);
    ctx.save();
    ctx.translate(x, h - pad + 12);
    ctx.rotate(-Math.PI / 6);
    ctx.fillText(labels[i], 0, 0);
    ctx.restore();
  }
}

function drawLine(ctx, w, h, pad, labels, values, color, filled) {
  const maxVal = Math.max(...values, 1);
  const maxY = getNiceMax(maxVal);
  drawAxes(ctx, w, h, pad, maxY, labels);

  const plotW = w - 2 * pad;
  const plotH = h - 2 * pad;

  function xAt(i) {
    return pad + (plotW * i) / Math.max(1, values.length - 1);
  }
  function yAt(v) {
    return h - pad - (plotH * v) / maxY;
  }

  if (filled) {
    ctx.beginPath();
    ctx.moveTo(xAt(0), h - pad);
    for (let i = 0; i < values.length; i++) {
      ctx.lineTo(xAt(i), yAt(values[i]));
    }
    ctx.lineTo(xAt(values.length - 1), h - pad);
    ctx.closePath();
    ctx.fillStyle = "rgba(37, 99, 235, 0.12)";
    ctx.fill();
  }

  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  for (let i = 0; i < values.length; i++) {
    const xi = xAt(i);
    const yi = yAt(values[i]);
    if (i === 0) ctx.moveTo(xi, yi);
    else ctx.lineTo(xi, yi);
  }
  ctx.stroke();

  ctx.fillStyle = color;
  for (let i = 0; i < values.length; i++) {
    ctx.beginPath();
    ctx.arc(xAt(i), yAt(values[i]), 3.5, 0, Math.PI * 2);
    ctx.fill();
  }
}

function render() {
  const data = parseDashboardData();
  if (!data || !data.series) return;

  document.querySelectorAll("canvas[data-chart]").forEach((canvas) => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const chartType = canvas.dataset.chart;
    const seriesKey = canvas.dataset.series;
    const seriesKey2 = canvas.dataset.series2;
    const s1 = data.series[seriesKey];
    const s2 = seriesKey2 ? data.series[seriesKey2] : null;
    if (!s1) return;

    const w = canvas.width || canvas.clientWidth;
    const h = canvas.height || canvas.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const pad = 34;
    ctx.clearRect(0, 0, w, h);

    if (chartType === "diverging" && s2) {
      drawDiverging(ctx, w, h, pad, s1.labels, s1.values, s2.values);
      return;
    }

    if (chartType === "bar") {
      if (s2) {
        drawBar(ctx, w, h, pad, s1.labels, s1.values, "#6c5ce7", 0, 2);
        drawBar(ctx, w, h, pad, s2.labels, s2.values, "#f5a25d", 1, 2);
      } else {
        const pay = canvas.dataset.accent === "payments";
        const fill = pay ? "#93c5fd" : "rgba(0, 206, 201, 0.85)";
        const stroke = pay ? "#60a5fa" : null;
        drawBar(ctx, w, h, pad, s1.labels, s1.values, fill, 0, 1, { stroke, lineWidth: 1 });
      }
      return;
    }

    if (chartType === "line") {
      const filled = canvas.dataset.filled === "1";
      drawLine(ctx, w, h, pad, s1.labels, s1.values, "#2563eb", filled);
    }
  });
}

window.addEventListener("load", render);
window.addEventListener("resize", () => {
  window.clearTimeout(window.__crmDashResize);
  window.__crmDashResize = window.setTimeout(render, 200);
});
