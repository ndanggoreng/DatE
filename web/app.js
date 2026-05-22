let i18n = {};

async function loadAppInfo() {
    try {
        const res = await fetch("/api/info");
        if (!res.ok) return;
        const info = await res.json();
        document.title = info.name + " (" + info.tagline + ")";
        const titleEl = document.getElementById("appTitle");
        const taglineEl = document.getElementById("appTagline");
        const versionEl = document.getElementById("appVersion");
        if (titleEl) titleEl.textContent = info.name;
        if (taglineEl) taglineEl.textContent = info.tagline;
        if (versionEl) versionEl.textContent = "v" + info.version;
    } catch (_) {}
}

async function loadI18n() {
    try {
        const res = await fetch("/api/i18n");
        if (!res.ok) return;
        const data = await res.json();
        i18n = data.strings || {};
        applyWebI18n();
    } catch (_) {}
}

function t(key) {
    return i18n[key] || key;
}

function applyWebI18n() {
    const pick = document.querySelector(".file-placeholder");
    const sendBtn = document.querySelector(".upload-btn");
    if (pick && i18n.web_pick_file) pick.textContent = i18n.web_pick_file;
    if (sendBtn && i18n.web_send) sendBtn.textContent = i18n.web_send;
}

function setProgress(percent, text) {
    document.getElementById("progressBar").style.width = percent + "%";
    document.getElementById("status").innerText = text || Math.round(percent) + "%";
}

async function pollServerStatus() {
    try {
        const res = await fetch("/api/status");
        if (!res.ok) return;
        const data = await res.json();
        if (data.uploading) {
            setProgress(
                data.upload_progress,
                (data.current_file || "") + " " + Math.round(data.upload_progress) + "%"
            );
        }
    } catch (_) {}
}

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert(t("web_pick_first"));
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload", true);
    xhr.setRequestHeader("X-Filename", encodeURIComponent(file.name));
    xhr.setRequestHeader("Content-Type", "application/octet-stream");

    const pollId = setInterval(pollServerStatus, 200);

    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            setProgress(percent);
        }
    };

    xhr.onload = function () {
        clearInterval(pollId);
        if (xhr.status === 200) {
            setProgress(100, t("web_upload_ok"));
        } else {
            let msg = t("web_upload_fail");
            try {
                const data = JSON.parse(xhr.responseText);
                if (data.message) msg = data.message;
            } catch (_) {}
            document.getElementById("status").innerText = msg;
        }
    };

    xhr.onerror = function () {
        clearInterval(pollId);
        document.getElementById("status").innerText = t("web_wifi_error");
    };

    setProgress(0, t("web_starting"));
    xhr.send(file);
}

document.getElementById("fileInput").addEventListener("change", function () {
    const file = this.files[0];
    const el = document.getElementById("fileName");
    if (file) {
        el.textContent = file.name;
        el.classList.add("has-file");
    } else {
        el.textContent = "";
        el.classList.remove("has-file");
    }
});

loadAppInfo();
loadI18n();
