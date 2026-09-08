const state = {
  situation: null,
  result: null,
};

const $ = (selector) => document.querySelector(selector);

function factsFromForm() {
  return [
    { key: "written_agreement_exists", label: "Written agreement exists", value: $("#fact-agreement").checked, source: "user-provided demo fact", confidence: 0.9 },
    { key: "departure_request_message_exists", label: "Message requesting departure exists", value: $("#fact-message").checked, source: "user-provided demo fact", confidence: 0.9 },
    { key: "requested_departure_days", label: "Requested departure timeframe", value: Number($("#fact-days").value) || null, source: "user-provided demo fact", confidence: 0.8 },
    { key: "jurisdiction", label: "Jurisdiction", value: $("#fact-jurisdiction").value.trim() || "Unspecified jurisdiction", source: "user-provided demo fact", confidence: 0.4 },
    { key: "formal_notice_received", label: "Formal notice received", value: $("#notice-yes").getAttribute("aria-pressed") === "true", source: "user-provided demo fact", confidence: 0.85 },
  ];
}

function situationFromForm() {
  return {
    narrative: $("#narrative").value.trim() || "A tenant is deciding how to respond to a sudden departure request.",
    facts: factsFromForm(),
    actions: [
      { id: "leave_now", title: "Leave immediately", description: "Move out on the requested timeline without first seeking more written detail." },
      { id: "clarify_first", title: "Ask for formal clarification", description: "Request written detail, preserve the record, and confirm the next decision point before acting." },
    ],
  };
}

function setStatus(message, loading = false, error = false) {
  const status = $("#app-status");
  status.innerHTML = `<span class="status-dot"></span> ${escapeHtml(message)}`;
  status.classList.toggle("is-loading", loading);
  status.classList.toggle("is-error", error);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

async function postJson(url, body) {
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "The simulation could not be completed.");
  return payload;
}

function setNoticeControl(value) {
  $("#notice-no").setAttribute("aria-pressed", String(!value));
  $("#notice-yes").setAttribute("aria-pressed", String(value));
  $("#notice-caption").textContent = value ? "Current state: notice marked received" : "Current state: not recorded";
}

function updateFormFromSituation(situation) {
  const facts = Object.fromEntries(situation.facts.map((fact) => [fact.key, fact.value]));
  $("#fact-agreement").checked = Boolean(facts.written_agreement_exists);
  $("#fact-message").checked = Boolean(facts.departure_request_message_exists);
  $("#fact-days").value = facts.requested_departure_days ?? "";
  $("#fact-jurisdiction").value = facts.jurisdiction ?? "";
  setNoticeControl(Boolean(facts.formal_notice_received));
  $("#narrative").value = situation.narrative;
}

function renderConstraints(constraints) {
  $("#constraint-list").innerHTML = constraints.map((constraint) => `<span class="constraint-chip is-${constraint.status}"><b>${escapeHtml(constraint.status)}</b>${escapeHtml(constraint.title)}</span>`).join("");
}

function renderBranch(branch, changed) {
  const actionLetter = branch.action.id === "leave_now" ? "A" : "B";
  const consequenceHtml = branch.consequences.map((consequence) => `<div class="consequence-item"><b>${escapeHtml(consequence.title)}</b><p>${escapeHtml(consequence.detail)}</p></div>`).join("");
  const dependencies = branch.dependencies.map((dependency) => `<span class="dependency">${escapeHtml(dependency)}</span>`).join("");
  const steps = branch.steps.map((step) => `<div class="timeline-item"><div class="timeline-rail"></div><div class="timeline-copy"><b>${escapeHtml(step.label)}</b><p>${escapeHtml(step.detail)}</p></div></div>`).join("");
  return `<article class="branch-card ${changed ? "changed" : ""}"><div class="branch-top"><div class="branch-kicker"><span>${actionLetter}</span> Scenario branch</div><h3>${escapeHtml(branch.headline)}</h3><p>${escapeHtml(branch.summary)}</p><div class="uncertainty-pill ${branch.uncertainty_label}"><span></span>${escapeHtml(branch.uncertainty_label)} uncertainty · ${branch.uncertainty_score}/100</div></div><div class="timeline">${steps}</div><div class="consequence-list"><span class="mini-heading">Possible consequences</span>${consequenceHtml}</div><div class="branch-footer"><span class="mini-heading">Depends on</span><p>These are dependencies to verify, not conclusions.</p><div class="dependency-list">${dependencies}</div></div></article>`;
}

function renderComparison(comparison) {
  return comparison.map((item) => {
    const letter = item.action_id === "leave_now" ? "A" : "B";
    const consequences = item.possible_consequences.map((itemText) => `<li>${escapeHtml(itemText)}</li>`).join("");
    const evidence = item.evidence_required.length ? item.evidence_required.map((itemText) => `<li>${escapeHtml(itemText)}</li>`).join("") : "<li>No additional evidence flagged by this state.</li>";
    const dependencies = item.dependencies.map((itemText) => `<li>${escapeHtml(itemText)}</li>`).join("");
    return `<article class="comparison-card"><h3><span>${letter}</span>${escapeHtml(item.action_title)}</h3><div class="comparison-row"><label>Possible consequences</label><ul>${consequences}</ul></div><div class="comparison-row"><label>Evidence required</label><ul>${evidence}</ul></div><div class="comparison-row"><label>Uncertainty</label><p>${escapeHtml(item.uncertainty)}</p></div><div class="comparison-row"><label>Dependencies</label><ul>${dependencies}</ul></div><div class="comparison-row"><label>Suggested next step</label><p class="comparison-next">${escapeHtml(item.suggested_next_step)}</p></div></article>`;
  }).join("");
}

function renderEvidenceList(selector, items, emptyText) {
  $(selector).innerHTML = items.length ? items.map((item) => `<div class="evidence-item"><b>${escapeHtml(item.label)}</b><p>${escapeHtml(item.why)}</p><small>${escapeHtml(item.source_hint || "Track the source and date")}</small></div>`).join("") : `<div class="evidence-item"><p>${emptyText}</p></div>`;
}

function renderResult(result, previousResult = null) {
  state.result = result;
  state.situation = result.normalized_situation;
  updateFormFromSituation(state.situation);
  $("#empty-state").hidden = true;
  $("#results").hidden = false;
  $("#simulation-id").textContent = `RUN ${result.simulation_id.toUpperCase()}`;
  $("#state-narrative").textContent = result.normalized_situation.narrative;
  renderConstraints(result.constraints);
  const changed = Boolean(result.graph_changed);
  $("#branch-grid").innerHTML = result.branches.map((branch) => renderBranch(branch, changed)).join("");
  $("#comparison-grid").innerHTML = renderComparison(result.comparison);
  renderEvidenceList("#supported-evidence", result.supported_evidence, "No evidence is currently marked supported.");
  renderEvidenceList("#missing-evidence", result.missing_evidence, "The current state has no missing item in this category.");
  renderEvidenceList("#uncertain-evidence", result.uncertain_evidence, "No evidence is currently marked uncertain.");
  $("#next-step-list").innerHTML = result.next_steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("");
  const changeBanner = $("#change-banner");
  if (result.graph_changed) {
    const factValue = (value) => typeof value === "boolean" ? (value ? "Yes" : "No") : String(value ?? "Unknown");
    $("#change-title").textContent = `Graph recomputed: ${factValue(result.changed_from)} → ${factValue(result.changed_to)}`;
    $("#change-detail").textContent = result.changed_because;
    changeBanner.hidden = false;
  } else {
    changeBanner.hidden = true;
  }
  setStatus(result.graph_changed ? "Counterfactual applied · downstream paths changed" : "Simulation complete · two scenario branches mapped");
  if (previousResult && result.graph_changed) $("#branch-grid").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function simulateDecision() {
  setStatus("Building decision state…", true);
  try {
    const situation = situationFromForm();
    const result = await postJson("/api/simulate", { situation });
    renderResult(result);
  } catch (error) {
    setStatus(error.message, false, true);
  }
}

async function applyCounterfactual(value) {
  if (!state.result) {
    setNoticeControl(value);
    return;
  }
  const currentNotice = factsFromForm().find((fact) => fact.key === "formal_notice_received")?.value;
  if (currentNotice === value) return;
  setStatus("Recomputing changed decision graph…", true);
  try {
    const previousResult = state.result;
    const result = await postJson("/api/counterfactual", { situation: situationFromForm(), fact_key: "formal_notice_received", new_value: value });
    renderResult(result, previousResult);
  } catch (error) {
    setStatus(error.message, false, true);
  }
}

function resetDemo() {
  state.result = null;
  state.situation = null;
  $("#narrative").value = "A tenant receives a sudden request from a landlord to leave within a short period. The tenant is deciding whether to leave now or seek formal clarification first.";
  $("#fact-agreement").checked = true;
  $("#fact-message").checked = true;
  $("#fact-days").value = 14;
  $("#fact-jurisdiction").value = "Demo jurisdiction";
  setNoticeControl(false);
  $("#empty-state").hidden = false;
  $("#results").hidden = true;
  setStatus("Ready to map your decision");
}

$("#simulate-button").addEventListener("click", simulateDecision);
$("[data-run-simulate]").addEventListener("click", simulateDecision);
$("#reset-button").addEventListener("click", resetDemo);
$("#notice-no").addEventListener("click", () => applyCounterfactual(false));
$("#notice-yes").addEventListener("click", () => applyCounterfactual(true));
