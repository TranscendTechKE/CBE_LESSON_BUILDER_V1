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

function setStatus(message, error = false) {
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
  console.log("STATE BEFORE GENERATION:", JSON.stringify(state, null, 2));
  console.log("SELECTED UNIT:", state.selectedUnit);
  console.log("DOCUMENT ID:", state.documentId);

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
      headers: { "Content-Type": "application/json" },
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

  $("planTitle").textContent =
    `${plan.sub_strand || "CBE Lesson Plan"}`;

  const developmentSteps =
    plan.lesson_development?.steps || [];

  const developmentHtml = developmentSteps.map(step => `
    <div class="flow-item">
      <strong>
        Step ${step.number}: ${escapeHtml(step.title)}
        (${step.duration_minutes} minutes)
      </strong>
      <ul>
        ${(step.activities || [])
      .map(activity => `<li>${escapeHtml(activity)}</li>`)
      .join("")}
      </ul>
    </div>
  `).join("");

  $("lessonContent").innerHTML = `

    <div class="plan-section">
      <h3>Lesson Information</h3>

      <p><strong>School:</strong>
        ${escapeHtml(plan.school)}
      </p>

      <p><strong>Teacher:</strong>
        ${escapeHtml(plan.teacher)}
      </p>

      <p><strong>Grade:</strong>
        ${escapeHtml(plan.grade)}
      </p>

      <p><strong>Learning Area:</strong>
        ${escapeHtml(plan.learning_area)}
      </p>

      <p><strong>Date:</strong>
        ${escapeHtml(plan.date)}
      </p>

      <p><strong>Time:</strong>
        ${escapeHtml(plan.time)}
      </p>

      <p><strong>Duration:</strong>
        ${escapeHtml(plan.duration_minutes)} minutes
      </p>

      <p><strong>Class Size:</strong>
        ${escapeHtml(plan.roll || "Not specified")}
      </p>

      <p><strong>Lesson Number:</strong>
        ${escapeHtml(plan.lesson_number)}
      </p>
    </div>

    <div class="plan-section">
      <h3>Curriculum Anchor</h3>

      <p><strong>Theme:</strong>
        ${escapeHtml(plan.theme)}
      </p>

      <p><strong>Strand:</strong>
        ${escapeHtml(plan.strand)}
      </p>

      <p><strong>Sub-strand:</strong>
        ${escapeHtml(plan.sub_strand)}
      </p>

      <p><strong>Source PDF pages:</strong>
        ${(plan.source_pages || []).join(", ") || "Not recorded"}
      </p>

      <p><strong>Source document:</strong>
        ${escapeHtml(plan.source_document || "Not recorded")}
      </p>
    </div>

    ${listBlock(
    "Specific Learning Outcomes",
    plan.specific_learning_outcomes
  )}

    ${listBlock(
    "Key Inquiry Questions",
    plan.key_inquiry_questions
  )}

    ${tagBlock(
    "Core Competencies",
    plan.core_competencies
  )}

    ${tagBlock(
    "Pertinent and Contemporary Issues",
    plan.pcis
  )}

    ${tagBlock(
    "Values",
    plan.values
  )}

    ${tagBlock(
    "Links to Other Subjects",
    plan.links_to_other_subjects
  )}

    ${tagBlock(
    "Learning Resources",
    plan.learning_resources
  )}

    <div class="plan-section">
      <h3>Lesson Flow</h3>

      <div class="flow-item">
        <strong>
          Introduction
          (${escapeHtml(plan.introduction?.duration_minutes || 0)} minutes)
        </strong>

        <ul>
          ${(plan.introduction?.activities || [])
      .map(activity => `<li>${escapeHtml(activity)}</li>`)
      .join("")}
        </ul>
      </div>

      <div class="flow-item">
        <strong>
          Lesson Development
          (${escapeHtml(plan.lesson_development?.duration_minutes || 0)} minutes)
        </strong>

        ${developmentHtml}
      </div>

      <div class="flow-item">
        <strong>
          Conclusion
          (${escapeHtml(plan.conclusion?.duration_minutes || 0)} minutes)
        </strong>

        <ul>
          ${(plan.conclusion?.activities || [])
      .map(activity => `<li>${escapeHtml(activity)}</li>`)
      .join("")}
        </ul>
      </div>
    </div>

    ${listBlock(
        "Assessment",
        plan.assessment
      )}

    ${listBlock(
        "Assessment Approaches",
        plan.assessment_approaches
      )}

    ${listBlock(
        "Extended Activities",
        plan.extended_activities
      )}

    ${listBlock(
        "Reflection",
        plan.reflection
      )}

    <div class="plan-section">
      <h3>Teacher Self-Evaluation</h3>

      <p><strong>What went well:</strong>
        ${escapeHtml(plan.teacher_self_evaluation?.what_went_well)}
      </p>

      <p><strong>Areas for improvement:</strong>
        ${escapeHtml(plan.teacher_self_evaluation?.areas_for_improvement)}
      </p>

      <p><strong>Learners needing support:</strong>
        ${escapeHtml(plan.teacher_self_evaluation?.learners_needing_support)}
      </p>

      <p><strong>Action for next lesson:</strong>
        ${escapeHtml(plan.teacher_self_evaluation?.action_for_next_lesson)}
      </p>

      <p><strong>Teacher signature:</strong>
        ${escapeHtml(plan.teacher_self_evaluation?.teacher_signature)}
      </p>
    </div>
  `;

  $("lessonOutput").scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
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
  return String(value ?? "").replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
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
