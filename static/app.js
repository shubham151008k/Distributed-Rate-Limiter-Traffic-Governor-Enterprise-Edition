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
    $("server-status").textContent = "Connected to the server.";
    const rows = stats.recent.map((r) =>
      `<tr><td>${r.client}</td><td>${r.allowed ? "Allowed" : "Denied"}</td><td>${r.remaining_tokens}</td></tr>`
    ).join("");
    $("recent").innerHTML = rows || '<tr><td colspan="3">No requests yet</td></tr>';
    const status = await api("/api/status?client=" + encodeURIComponent(client()));
    $("gauge-text").textContent = `${status.remaining_tokens} / ${status.capacity}`;
    $("gauge").style.width = (status.remaining_tokens / status.capacity) * 100 + "%";
  } catch (e) {
    $("server-status").textContent = "Cannot reach the server — is python server.py running?";
  }
}

$("send").addEventListener("click", async () => {
  try { show(await api("/api/request", { client: client() })); await refresh(); }
  catch (e) { alert(e.message); }
});

$("burst").addEventListener("click", async () => {
  try {
    const out = await api("/api/burst", { client: client(), count: 15 });
    const last = out.results[out.results.length - 1];
    show(last);
    $("retry-note").textContent = `Burst ×15: ${out.allowed} allowed, ${out.denied} denied.`;
    await refresh();
  } catch (e) { alert(e.message); }
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
