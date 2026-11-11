// Demo page logic: small fetch calls, then update gauge, badge, counters, list.
// No build step, no framework - plain JavaScript, as the PRD requires.
const $ = (id) => document.getElementById(id);

function client() {
  const custom = $("custom-client").value.trim();
  return custom || $("client").value;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function show(result) {
  const badge = $("badge");
  badge.textContent = result.allowed ? "✔ Allowed" : "✖ Denied";
  badge.className = "badge fs-6 " + (result.allowed ? "bg-success" : "bg-danger");
  $("gauge-text").textContent = `${result.remaining_tokens} / ${result.capacity}`;
  const pct = (result.remaining_tokens / result.capacity) * 100;
  $("gauge").style.width = pct + "%";
  $("gauge-wrap").setAttribute("aria-valuemax", result.capacity);
  $("gauge-wrap").setAttribute("aria-valuenow", result.remaining_tokens);
  $("retry-note").textContent = result.allowed
    ? ""
    : `Denied — retry in about ${result.retry_after_ms} ms.`;
}

async function refresh() {
  try {
    const stats = await api("/api/stats");
    $("allowed-count").textContent = stats.allowed;
    $("denied-count").textContent = stats.denied;
    const serverStatus = $("server-status");
    serverStatus.textContent = "● Server Connected";
    serverStatus.style.color = "#dcfce7";
    serverStatus.style.background = "rgba(22, 163, 74, 0.18)";

const recentTable = $("recent");
recentTable.replaceChildren();

if (stats.recent.length === 0) {
  const row = document.createElement("tr");
  const cell = document.createElement("td");

  cell.colSpan = 3;
  cell.textContent = "No requests yet";

  row.appendChild(cell);
  recentTable.appendChild(row);
} else {
  stats.recent.forEach((r) => {
    const row = document.createElement("tr");

    const clientCell = document.createElement("td");
    clientCell.textContent = r.client;

    const decisionCell = document.createElement("td");
    decisionCell.textContent = r.allowed ? "Allowed" : "Denied";

    const remainingCell = document.createElement("td");
    remainingCell.textContent = r.remaining_tokens;

    row.append(clientCell, decisionCell, remainingCell);
    recentTable.appendChild(row);
  });
}
    const status = await api("/api/status?client=" + encodeURIComponent(client()));
    $("gauge-text").textContent = `${status.remaining_tokens} / ${status.capacity}`;
    $("gauge").style.width = (status.remaining_tokens / status.capacity) * 100 + "%";
  } catch (e) {
    const serverStatus = $("server-status");
    serverStatus.textContent = "● Server Disconnected";
    serverStatus.style.color = "#fee2e2";
    serverStatus.style.background = "rgba(220, 38, 38, 0.18)";
  }
}

$("send").addEventListener("click", async () => {
  $("request-error").textContent = "";

  try {
    show(await api("/api/request", { client: client() }));
    await refresh();
  } catch (e) {
    $("request-error").textContent = "Request failed: " + e.message;
  }
});


$("burst").addEventListener("click", async () => {
  $("request-error").textContent = "";

  try {
    const out = await api("/api/burst", {
      client: client(),
      count: 15
    });

    const last = out.results[out.results.length - 1];
    show(last);

    $("retry-note").textContent =
      `Burst ×15: ${out.allowed} allowed, ${out.denied} denied.`;

    await refresh();
  } catch (e) {
    $("request-error").textContent = "Burst failed: " + e.message;
  }
});


$("apply-config").addEventListener("click", async () => {
  $("config-error").textContent = ""; $("config-ok").textContent = "";
  try {
    const cfg = await api("/api/config", {
      capacity: Number($("capacity").value),
      refill_rate: Number($("refill").value),
    });
    $("active-config").textContent = `capacity ${cfg.capacity}, refill ${cfg.refill_rate} / second`;
    $("config-ok").textContent = "Config applied. Buckets were reset.";
    await refresh();
  } catch (e) { $("config-error").textContent = e.message; }
});

$("reset").addEventListener("click", async () => {
  if (!confirm("Reset all buckets and counters?")) return;
  await api("/api/reset", {});
  $("badge").textContent = "No requests yet";
  $("badge").className = "badge bg-secondary fs-6";
  await refresh();
});

$("client").addEventListener("change", refresh);
refresh();
