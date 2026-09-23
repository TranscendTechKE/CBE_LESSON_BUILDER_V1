window.CBE = {
    state: {
        curriculum: null,
        lesson: null
    },

    $(selector) {
        return document.querySelector(selector);
    },

    show(selector) {
        this.$(selector)?.classList.remove("hidden");
    },

    hide(selector) {
        this.$(selector)?.classList.add("hidden");
    },

    setStatus(message, error = false) {
        const el = this.$("#status");
        if (!el) return;
        el.textContent = message;
        el.style.color = error ? "#b42318" : "";
    }
};
