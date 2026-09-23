document.addEventListener("DOMContentLoaded", () => {
    CBE.$("#generateBtn").addEventListener("click", generateLesson);
    CBE.$("#printBtn").addEventListener("click", () => window.print());
});


async function generateLesson() {
    const c = CBE.state.curriculum;

    if (!c) {
        CBE.setStatus("Process a curriculum PDF first.", true);
        return;
    }

    const updated = {
        ...c,
        learning_area: CBE.$("#learningArea").value,
        grade: CBE.$("#grade").value,
        strand: CBE.$("#strand").value,
        sub_strand: CBE.$("#subStrand").value,
        learning_outcomes: lines("#outcomes"),
        inquiry_questions: lines("#questions"),
        learning_experiences: lines("#experiences"),
        resources: lines("#resources")
    };

    CBE.state.curriculum = updated;

    CBE.setStatus("Generating lesson plan…");

    try {
        const response = await fetch("/api/generate-lesson", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(updated)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Generation failed.");
        }

        CBE.state.lesson = data.lesson;
        renderLesson(data.lesson);
        CBE.show("#lessonSection");
        CBE.setStatus("Lesson plan generated. Edit it before printing.");
    } catch (error) {
        CBE.setStatus(error.message, true);
    }
}


function lines(selector) {
    return CBE.$(selector).value
        .split("\n")
        .map(x => x.trim())
        .filter(Boolean);
}


function renderLesson(l) {
    const editor = CBE.$("#lessonEditor");

    editor.innerHTML = `
        <div class="lesson-sheet">
            <label>Lesson Title
                <input data-key="title" value="${esc(l.title)}">
            </label>

            <div class="grid two">
                ${field("Learning Area", "learning_area", l.learning_area)}
                ${field("Grade", "grade", l.grade)}
                ${field("Strand", "strand", l.strand)}
                ${field("Sub-strand", "sub_strand", l.sub_strand)}
                ${field("Duration", "duration", l.duration)}
            </div>

            ${textareaField("Specific Learning Outcomes", "specific_learning_outcomes", l.specific_learning_outcomes)}
            ${textareaField("Core Competencies", "core_competencies", l.core_competencies)}
            ${textareaField("Values", "values", l.values)}
            ${textareaField("PCIs", "pcis", l.pcis)}
            ${textareaField("Resources", "resources", l.resources)}

            ${textField("Introduction", "introduction", l.introduction)}
            ${textField("Development", "development", l.development)}
            ${textField("Learner Activities", "learner_activities", l.learner_activities)}
            ${textField("Assessment", "assessment", l.assessment)}
            ${textField("Differentiation", "differentiation", l.differentiation)}
            ${textField("Reflection", "reflection", l.reflection)}
            ${textField("Homework", "homework", l.homework)}
        </div>
    `;
}


function field(label, key, value) {
    return `<label>${label}<input data-key="${key}" value="${esc(value || "")}"></label>`;
}


function textField(label, key, value) {
    return `<label>${label}<textarea rows="4" data-key="${key}">${esc(value || "")}</textarea></label>`;
}


function textareaField(label, key, values) {
    return `<label>${label}<textarea rows="5" data-list-key="${key}">${esc((values || []).join("\n"))}</textarea></label>`;
}


function esc(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
}
