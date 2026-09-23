document.addEventListener("DOMContentLoaded", () => {
    const fileInput = CBE.$("#pdfFile");
    const processBtn = CBE.$("#processBtn");

    processBtn.addEventListener("click", async () => {
        const file = fileInput.files[0];

        if (!file) {
            CBE.setStatus("Choose a PDF first.", true);
            return;
        }

        const form = new FormData();
        form.append("file", file);

        CBE.setStatus("Processing PDF…");

        try {
            const response = await fetch("/api/upload-curriculum", {
                method: "POST",
                body: form
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Upload failed.");
            }

            CBE.state.curriculum = data.curriculum;
            populateCurriculum(data.curriculum, data.warnings || []);

            CBE.show("#curriculumSection");
            CBE.setStatus("Curriculum extracted. Review the fields before generating the lesson.");
        } catch (error) {
            CBE.setStatus(error.message, true);
        }
    });
});


function populateCurriculum(c, warnings) {
    CBE.$("#learningArea").value = c.learning_area || "";
    CBE.$("#grade").value = c.grade || "";
    CBE.$("#strand").value = c.strand || "";
    CBE.$("#subStrand").value = c.sub_strand || "";
    CBE.$("#outcomes").value = (c.learning_outcomes || []).join("\n");
    CBE.$("#questions").value = (c.inquiry_questions || []).join("\n");
    CBE.$("#experiences").value = (c.learning_experiences || []).join("\n");
    CBE.$("#resources").value = (c.resources || []).join("\n");
    CBE.$("#pageCount").textContent = `${c.page_count || 0} pages`;

    CBE.$("#warnings").innerHTML = warnings.map(
        warning => `<div>⚠ ${escapeHtml(warning)}</div>`
    ).join("");
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
