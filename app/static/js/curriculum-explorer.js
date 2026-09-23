const state = {
  documentId: null,
  document: null,
  selectedTheme: null,
  selectedUnit: null,
  lessonPlan: null
};

const $ = (id) => document.getElementById(id);

$("pdfFile").addEventListener("change", (e) => {
  const file = e.target.files[0];
  $("fileName").textContent = file ? file.name : "Choose curriculum PDF";
});

$("uploadBtn").addEventListener("click", uploadPdf);
$("themeSelect").addEventListener("change", selectTheme);
$("strandSelect").addEventListener("change", selectStrand);
$("unitSelect").addEventListener("change", selectUnit);
$("generateBtn").addEventListener("click", generateLessonPlan);
$("copyBtn").addEventListener("click", copyJson);

async function uploadPdf() {
  const file = $("pdfFile").files[0];
  if (!file) return setStatus("Choose a curriculum PDF first.");

  const form = new FormData();
  form.append("file", file);
  setStatus("Processing the PDF page-by-page…");

  try {
    const response = await fetch("/api/curriculum/upload", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "PDF processing failed.");

    state.documentId = data.document_id;
    state.document = data.summary;
    renderSummary(data.summary);
    populateThemes(data.summary.themes);

    $("explorer").classList.remove("hidden");
    $("generator").classList.add("hidden");
    $("lessonOutput").classList.add("hidden");
    setStatus(`Processed ${data.summary.page_count} pages and found ${data.summary.theme_count} themes / ${data.summary.unit_count} units.`);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function setStatus(message, error=false) {
  $("uploadStatus").textContent = message;
  $("uploadStatus").style.color = error ? "#b42318" : "";
}

function renderSummary(summary) {
  $("documentSummary").innerHTML = `
    <strong>${escapeHtml(summary.learning_area || "Learning Area")}</strong>
    · ${escapeHtml(summary.grade || "")}
    · ${summary.page_count} PDF pages
    · curriculum extraction begins at PDF page ${summary.extraction_start_page ?? "—"}
  `;
}

function populateThemes(themes) {
  $("themeSelect").innerHTML = `<option value="">Select theme</option>` +
    themes.map(t => `<option value="${escapeAttr(t.code)}">${escapeHtml(t.code)} — ${escapeHtml(t.title)}</option>`).join("");
  $("strandSelect").innerHTML = `<option value="">Select strand</option>`;
  $("unitSelect").innerHTML = `<option value="">Select sub-strand</option>`;
  $("strandSelect").disabled = true;
  $("unitSelect").disabled = true;
  $("unitPreview").classList.add("hidden");
  $("generateBtn").disabled = true;
}

async function selectTheme() {
  const code = $("themeSelect").value;
  $("strandSelect").disabled = true;
  $("unitSelect").disabled = true;
  $("unitPreview").classList.add("hidden");
  $("generateBtn").disabled = true;
  if (!code) return;

  state.selectedTheme = code;
  const units = await fetchJson(`/api/curriculum/${state.documentId}/themes/${encodeURIComponent(code)}/units`);

  const strands = [];
  const seen = new Set();
  for (const unit of units) {
    if (!seen.has(unit.strand_code)) {
      seen.add(unit.strand_code);
      strands.push({ code: unit.strand_code, name: unit.strand });
    }
  }

  $("strandSelect").innerHTML = `<option value="">Select strand</option>` +
    strands.map(s => `<option value="${escapeAttr(s.code)}">${escapeHtml(s.code)} — ${escapeHtml(s.name)}</option>`).join("");
  $("strandSelect").disabled = false;
  $("unitSelect").innerHTML = `<option value="">Select sub-strand</option>`;
}

async function selectStrand() {
  const strandCode = $("strandSelect").value;
  $("unitSelect").disabled = true;
  $("unitPreview").classList.add("hidden");
  $("generateBtn").disabled = true;
  if (!strandCode) return;

  const units = await fetchJson(`/api/curriculum/${state.documentId}/themes/${encodeURIComponent(state.selectedTheme)}/units`);
  const filtered = units.filter(u => u.strand_code === strandCode);

  $("unitSelect").innerHTML = `<option value="">Select sub-strand</option>` +
    filtered.map(u => `<option value="${escapeAttr(u.sub_strand_code)}">${escapeHtml(u.sub_strand_code)} — ${escapeHtml(u.sub_strand)}${u.lessons ? ` (${u.lessons} Lessons)` : ""}</option>`).join("");
  $("unitSelect").disabled = false;
}

async function selectUnit() {
  const code = $("unitSelect").value;
  $("generateBtn").disabled = true;
  $("unitPreview").classList.add("hidden");
  if (!code) return;

  const unit = await fetchJson(`/api/curriculum/${state.documentId}/unit/${encodeURIComponent(code)}`);
  state.selectedUnit = unit;

  $("unitPreview").innerHTML = `
    <h3>${escapeHtml(unit.sub_strand_code)} — ${escapeHtml(unit.sub_strand)}</h3>
    <p><strong>Strand:</strong> ${escapeHtml(unit.strand_code)} — ${escapeHtml(unit.strand)}</p>
    <p><strong>Lessons allocated:</strong> ${unit.lessons ?? "Not specified"}</p>
    ${listBlock("Specific Learning Outcomes", unit.specific_learning_outcomes)}
    ${listBlock("Key Inquiry Questions", unit.key_inquiry_questions)}
    ${tagBlock("Core Competencies", unit.core_competencies)}
    ${tagBlock("PCIs", unit.pertinent_and_contemporary_issues)}
    ${tagBlock("Values", unit.values)}
    ${tagBlock("Links to Other Subjects", unit.links_to_other_subjects)}
    <small>Source PDF pages: ${(unit.source_pdf_pages || []).join(", ")}</small>
  `;
  $("unitPreview").classList.remove("hidden");
  $("generator").classList.remove("hidden");
  $("generateBtn").disabled = false;
}

async function generateLessonPlan() {
  if (!state.selectedUnit) return;

  const payload = {
    document_id: state.documentId,
    sub_strand_code: state.selectedUnit.sub_strand_code,
    teacher_name: $("teacherName").value,
    school_name: $("schoolName").value,
    lesson_date: $("lessonDate").value,
    duration_minutes: Number($("duration").value),
    class_size: $("classSize").value ? Number($("classSize").value) : null,
    lesson_number: Number($("lessonNumber").value)
  };

  $("generateBtn").disabled = true;
  $("generateBtn").textContent = "Generating…";

  try {
    const response = await fetch("/api/curriculum/lesson-plan", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const plan = await response.json();
    if (!response.ok) throw new Error(plan.detail || "Generation failed.");
    state.lessonPlan = plan;
    renderLessonPlan(plan);
  } catch (error) {
    alert(error.message);
  } finally {
    $("generateBtn").disabled = false;
    $("generateBtn").textContent = "Generate CBE Lesson Plan";
  }
}

function renderLessonPlan(plan) {
  $("lessonOutput").classList.remove("hidden");
  $("planTitle").textContent = `${plan.curriculum.sub_strand_code} — ${plan.curriculum.sub_strand}`;

  $("lessonContent").innerHTML = `
    <div class="plan-section">
      <h3>Curriculum Anchor</h3>
      <p><strong>Theme:</strong> ${escapeHtml(plan.curriculum.theme_code)} — ${escapeHtml(plan.curriculum.theme)}</p>
      <p><strong>Strand:</strong> ${escapeHtml(plan.curriculum.strand_code)} — ${escapeHtml(plan.curriculum.strand)}</p>
      <p><strong>Sub-strand:</strong> ${escapeHtml(plan.curriculum.sub_strand_code)} — ${escapeHtml(plan.curriculum.sub_strand)}</p>
      <p><strong>Source PDF pages:</strong> ${(plan.curriculum.source_pdf_pages || []).join(", ")}</p>
    </div>

    ${listBlock("Specific Learning Outcomes", plan.specific_learning_outcomes)}
    ${listBlock("Lesson Objectives", plan.lesson_objectives.map(x => x.objective))}
    ${listBlock("Key Inquiry Questions", plan.key_inquiry_questions)}
    ${tagBlock("Core Competencies", plan.core_competencies)}
    ${tagBlock("Pertinent and Contemporary Issues", plan.pertinent_and_contemporary_issues)}
    ${tagBlock("Values", plan.values)}

    <div class="plan-section">
      <h3>Lesson Flow</h3>
      <div class="flow-item"><strong>Introduction</strong>${escapeHtml(plan.lesson_flow.introduction.activity)}</div>
      ${plan.lesson_flow.development.activities.map(a => `<div class="flow-item"><strong>Activity ${a.step}</strong>${escapeHtml(a.activity)}</div>`).join("")}
      <div class="flow-item"><strong>Assessment</strong>${escapeHtml(plan.lesson_flow.assessment.activity)}</div>
      <div class="flow-item"><strong>Reflection</strong>${escapeHtml(plan.lesson_flow.reflection.teacher_prompt)}</div>
    </div>

    ${listBlock("Assessment Approaches", plan.assessment.approaches)}
    ${listBlock("Resources", plan.resources)}
  `;

  $("lessonOutput").scrollIntoView({behavior:"smooth", block:"start"});
}

function listBlock(title, items) {
  if (!items || !items.length) return "";
  return `<div class="plan-section"><h3>${escapeHtml(title)}</h3><ul>${items.map(x => `<li>${escapeHtml(typeof x === "string" ? x : x.objective)}</li>`).join("")}</ul></div>`;
}

function tagBlock(title, items) {
  if (!items || !items.length) return "";
  return `<div class="plan-section"><h3>${escapeHtml(title)}</h3>${items.map(x => `<span class="tag">${escapeHtml(x)}</span>`).join("")}</div>`;
}

async function fetchJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed.");
  return data;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function escapeAttr(value) {
  return escapeHtml(value);
}

async function copyJson() {
  if (!state.lessonPlan) return;
  await navigator.clipboard.writeText(JSON.stringify(state.lessonPlan, null, 2));
  $("copyBtn").textContent = "Copied";
  setTimeout(() => $("copyBtn").textContent = "Copy JSON", 1200);
}
