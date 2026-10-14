const state = {
  documentId: null,
  document: null,
  profile: null,
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

    const profileResponse = await fetch(
      `/api/curriculum/${data.document_id}/profile`
    );

    const profile = await profileResponse.json();

    if (!profileResponse.ok) {
      throw new Error(
        profile.detail || "Could not load the curriculum profile."
      );
    }
    state.documentId = data.document_id;
    state.profile = profile;
    state.document = data.summary;
    renderSummary(data.summary);
    populateThemes(
      state.profile.content_nodes,
      state.profile.hierarchy_labels
    );
    console.log("PROFILE HIERARCHY:", state.profile.hierarchy_labels);
    console.log("PROFILE FIRST NODE:", state.profile.content_nodes[0]);

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


function populateThemes(nodes, labels = []) {
  const names = [
    labels[0] || "Theme",
    labels[1] || "Strand",
    labels[2] || "Sub-strand"
  ];

  $("themeLabel").textContent = names[0];
  $("strandLabel").textContent = names[1];
  $("unitLabel").textContent = names[2];

  // Hide the third selector when the curriculum has fewer than 3 levels.
  $("unitSelect").closest("label").hidden = labels.length < 3;

  $("themeSelect").innerHTML =
    `<option value="">Select ${escapeHtml(names[0].toLowerCase())}</option>` +
    nodes.map(node =>
      `<option value="${escapeAttr(node.code)}">${escapeHtml(node.code)} — ${escapeHtml(node.title)}</option>`
    ).join("");

  $("strandSelect").innerHTML =
    `<option value="">Select ${escapeHtml(names[1].toLowerCase())}</option>`;

  $("unitSelect").innerHTML =
    `<option value="">Select ${escapeHtml(names[2].toLowerCase())}</option>`;

  $("strandSelect").disabled = true;
  $("unitSelect").disabled = true;

  state.selectedTheme = null;
  state.selectedUnit = null;

  $("unitPreview").classList.add("hidden");
  $("generator").classList.add("hidden");
  $("lessonOutput").classList.add("hidden");
  $("generateBtn").disabled = true;
}

function resetUnitSelection() {
  state.selectedUnit = null;
  $("unitPreview").classList.add("hidden");
  $("generator").classList.add("hidden");
  $("lessonOutput").classList.add("hidden");
  $("generateBtn").disabled = true;
}

async function showSelectedUnit(code) {
  resetUnitSelection();
  if (!code) return;

  try {
    const unit = await fetchJson(
      `/api/curriculum/${state.documentId}/unit/${encodeURIComponent(code)}`
    );

    state.selectedUnit = unit;

    $("unitPreview").innerHTML = `
      <h3>${escapeHtml(unit.sub_strand_code || unit.code || "")} — ${escapeHtml(unit.sub_strand || unit.title || "")}</h3>
      <p><strong>${escapeHtml(state.profile.hierarchy_labels[0] || "Section")}:</strong> ${escapeHtml(unit.theme_title || unit.strand || "Not specified")}</p>
      <p><strong>Strand:</strong> ${escapeHtml(unit.strand_code || "")} ${escapeHtml(unit.strand || "")}</p>
      <p><strong>Learning area:</strong> ${escapeHtml(unit.learning_area || state.profile.learning_area || "Not specified")}</p>
      <p><strong>Lessons allocated:</strong> ${unit.lessons ?? "Not specified"}</p>
      ${listBlock("Specific Learning Outcomes", unit.specific_learning_outcomes)}
      ${listBlock("Suggested Learning Experiences", unit.suggested_learning_experiences)}
      ${listBlock("Key Inquiry Questions", unit.key_inquiry_questions)}
      ${tagBlock("Core Competencies", unit.core_competencies)}
      ${tagBlock("PCIs", unit.pertinent_and_contemporary_issues)}
      ${tagBlock("Values", unit.values)}
      ${tagBlock("Links to Other Subjects", unit.links_to_other_subjects)}
      <small>Source PDF pages: ${(unit.source_pdf_pages || unit.source_pages || []).join(", ")}</small>
    `;

    $("unitPreview").classList.remove("hidden");
    $("generator").classList.remove("hidden");
    $("generateBtn").disabled = false;
  } catch (error) {
    state.selectedUnit = null;
    $("unitPreview").innerHTML =
      `<p>Could not load this curriculum unit: ${escapeHtml(error.message || "Unknown error")}</p>`;
    $("unitPreview").classList.remove("hidden");
    $("generator").classList.add("hidden");
    $("generateBtn").disabled = true;
  }
}

function selectTheme() {
  const code = $("themeSelect").value;
  resetUnitSelection();

  state.selectedTheme = code || null;

  $("strandSelect").disabled = true;
  $("unitSelect").disabled = true;

  const theme = state.profile.content_nodes.find(
    node => node.code === code
  );

  const children = theme?.children || [];
  const labels = state.profile.hierarchy_labels || [];
  const strandLabel = labels[1] || "Strand";
  const unitLabel = labels[2] || "Sub-strand";

  $("strandSelect").innerHTML =
    `<option value="">Select ${escapeHtml(strandLabel.toLowerCase())}</option>` +
    children.map(node =>
      `<option value="${escapeAttr(node.code)}">${escapeHtml(node.code)} — ${escapeHtml(node.title)}</option>`
    ).join("");

  $("unitSelect").innerHTML =
    `<option value="">Select ${escapeHtml(unitLabel.toLowerCase())}</option>`;

  $("strandSelect").disabled = children.length === 0;

  // One-level hierarchy: the selected root is itself the content unit.
  if (code && labels.length === 1 && !children.length) {
    showSelectedUnit(code);
  }
}

function selectStrand() {
  const code = $("strandSelect").value;
  resetUnitSelection();

  $("unitSelect").disabled = true;

  const labels = state.profile.hierarchy_labels || [];
  const theme = state.profile.content_nodes.find(
    node => node.code === state.selectedTheme
  );

  const strand = theme?.children?.find(
    node => node.code === code
  );

  const children = strand?.children || [];

  // Two-level hierarchy: the second selector contains the selectable units.
  if (labels.length === 2) {
    if (code) showSelectedUnit(code);
    return;
  }

  // Three-level hierarchy: populate the third selector.
  $("unitSelect").innerHTML =
    `<option value="">Select ${escapeHtml((labels[2] || "Sub-strand").toLowerCase())}</option>` +
    children.map(node =>
      `<option value="${escapeAttr(node.code)}">${escapeHtml(node.code)} — ${escapeHtml(node.title)}${node.lessons ? ` (${node.lessons} Lessons)` : ""}</option>`
    ).join("");

  $("unitSelect").disabled = children.length === 0;
}

async function selectUnit() {
  await showSelectedUnit($("unitSelect").value);
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

async function downloadLessonPlanWord() {
  const plan = state.lessonPlan;
  if (!plan) {
    alert("Generate a lesson plan before downloading.");
    return;
  }

  const button = $("downloadWordBtn");
  button.disabled = true;
  button.textContent = "Preparing Word document…";

  try {
    const response = await fetch(
      "/api/curriculum/lesson-plan/export-docx",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan })
      }
    );

    if (!response.ok) {
      let message = "Word export failed.";
      try {
        const error = await response.json();
        message = error.detail || message;
      } catch (_) {}
      throw new Error(message);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = makeLessonPlanFilename(plan);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    alert(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Download Word";
  }
}

function filenamePart(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function makeLessonPlanFilename(plan) {
  const parts = [
    plan.grade,
    plan.theme,
    plan.strand,
    plan.sub_strand
  ]
    .map(filenamePart)
    .filter(Boolean);

  // If there is no theme, the empty theme is automatically omitted.
  return `${parts.join("_") || "CBE_Lesson_Plan"}.docx`;
}

$("downloadWordBtn").addEventListener(
  "click",
  downloadLessonPlanWord
);
