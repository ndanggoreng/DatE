let i18n = {};
let activeTab = "send";
let outgoingPollId = null;
let healthPollId = null;
let serverOnline = false;

const STATUS_TIMEOUT_MS = 4000;
const HEALTH_INTERVAL_MS = 2500;

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
        updateServerBanner();
    } catch (_) {}
}

function t(key) {
    return i18n[key] || key;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function applyWebI18n() {
    const pick = document.querySelector(".file-placeholder");
    const sendBtn = document.getElementById("sendBtn");
    const tabSend = document.getElementById("tabSend");
    const tabReceive = document.getElementById("tabReceive");
    const refreshBtn = document.getElementById("refreshBtn");
    const receiveHint = document.getElementById("receiveHint");
    if (pick && i18n.web_pick_file) pick.textContent = i18n.web_pick_file;
    if (sendBtn && i18n.web_send) sendBtn.textContent = i18n.web_send;
    if (tabSend && i18n.web_tab_send) tabSend.textContent = i18n.web_tab_send;
    if (tabReceive && i18n.web_tab_receive) tabReceive.textContent = i18n.web_tab_receive;
    if (refreshBtn && i18n.web_refresh) refreshBtn.textContent = i18n.web_refresh;
    if (receiveHint && i18n.web_receive_hint) receiveHint.textContent = i18n.web_receive_hint;
}

function updateServerBanner() {
    const banner = document.getElementById("serverBanner");
    if (!banner) return;
    if (serverOnline) {
        banner.classList.add("hidden");
        banner.textContent = "";
    } else {
        banner.classList.remove("hidden");
        banner.textContent = t("web_server_offline_short");
    }
}

function alertServerOffline() {
    alert(t("web_server_offline"));
}

async function checkServerOnline() {
    try {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), STATUS_TIMEOUT_MS);
        const res = await fetch("/api/status", {
            signal: ctrl.signal,
            cache: "no-store",
        });
        clearTimeout(timer);
        if (!res.ok) return false;
        const data = await res.json();
        return data.server_running !== false;
    } catch (_) {
        return false;
    }
}

function resetFileInput() {
    const fileInput = document.getElementById("fileInput");
    const el = document.getElementById("fileName");
    if (fileInput) fileInput.value = "";
    if (el) {
        el.textContent = "";
        el.classList.remove("has-file");
    }
}

function clearOutgoingList(offline) {
    const list = document.getElementById("outgoingList");
    const status = document.getElementById("receiveStatus");
    if (!list) return;
    list.innerHTML = "";
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = offline ? t("web_server_offline_short") : t("web_no_files");
    list.appendChild(li);
    if (status) status.innerText = "";
}

function setServerOnline(online) {
    const wasOnline = serverOnline;
    serverOnline = online;
    document.body.classList.toggle("server-offline", !online);
    updateServerBanner();

    if (!online) {
        clearOutgoingList(true);
        resetFileInput();
        const bar = document.getElementById("progressBar");
        const sendStatus = document.getElementById("status");
        if (bar) bar.style.width = "0%";
        if (sendStatus) sendStatus.innerText = "";
        if (outgoingPollId) {
            clearInterval(outgoingPollId);
            outgoingPollId = null;
        }
    } else if (!wasOnline && activeTab === "receive") {
        loadOutgoing(false);
        if (!outgoingPollId) {
            outgoingPollId = setInterval(() => loadOutgoing(false), 3000);
        }
    }
}

async function tickHealth() {
    const online = await checkServerOnline();
    setServerOnline(online);
}

function startHealthPoll() {
    tickHealth();
    if (healthPollId) clearInterval(healthPollId);
    healthPollId = setInterval(tickHealth, HEALTH_INTERVAL_MS);
}

async function requireServerOnline(showAlert) {
    const online = await checkServerOnline();
    setServerOnline(online);
    if (!online && showAlert) alertServerOffline();
    return online;
}

function setProgress(percent, text) {
    const bar = document.getElementById("progressBar");
    const status = document.getElementById("status");
    if (bar) bar.style.width = percent + "%";
    if (status) status.innerText = text || Math.round(percent) + "%";
}

function switchTab(name) {
    activeTab = name;
    document.querySelectorAll(".tab").forEach((el) => {
        el.classList.toggle("active", el.dataset.tab === name);
    });
    document.getElementById("panelSend").classList.toggle("active", name === "send");
    document.getElementById("panelReceive").classList.toggle("active", name === "receive");

    if (name === "receive") {
        requireServerOnline(true).then((online) => {
            if (online) {
                loadOutgoing(false);
                if (!outgoingPollId) {
                    outgoingPollId = setInterval(() => loadOutgoing(false), 3000);
                }
            }
        });
    }
}

document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

async function pollServerStatus() {
    if (!serverOnline) return;
    try {
        const res = await fetch("/api/status", { cache: "no-store" });
        if (!res.ok) {
            setServerOnline(false);
            return;
        }
        const data = await res.json();
        if (data.server_running === false) {
            setServerOnline(false);
            return;
        }
        if (data.uploading) {
            setProgress(
                data.upload_progress,
                (data.current_file || "") + " " + Math.round(data.upload_progress) + "%"
            );
        }
    } catch (_) {
        setServerOnline(false);
    }
}

async function uploadFile() {
    if (!(await requireServerOnline(true))) return;

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
        setServerOnline(false);
        alertServerOffline();
    };

    setProgress(0, t("web_starting"));
    xhr.send(file);
}

async function loadOutgoing(showAlertOnOffline) {
    const list = document.getElementById("outgoingList");
    const status = document.getElementById("receiveStatus");
    if (!list) return;

    if (!(await requireServerOnline(showAlertOnOffline))) {
        clearOutgoingList(true);
        return;
    }

    try {
        const res = await fetch("/api/outgoing", { cache: "no-store" });
        if (!res.ok) {
            setServerOnline(false);
            clearOutgoingList(true);
            if (showAlertOnOffline) alertServerOffline();
            return;
        }
        const data = await res.json();
        const files = data.files || [];
        list.innerHTML = "";
        if (!files.length) {
            const li = document.createElement("li");
            li.className = "empty";
            li.textContent = t("web_no_files");
            list.appendChild(li);
            if (status) status.innerText = "";
            return;
        }
        files.forEach((f) => {
            const li = document.createElement("li");
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "download-item";
            btn.innerHTML =
                "<span class='name'>" +
                f.name +
                "</span><span class='size'>" +
                formatSize(f.size) +
                "</span>";
            btn.addEventListener("click", () => downloadFile(f.url, f.name));
            li.appendChild(btn);
            list.appendChild(li);
        });
        if (status) status.innerText = "";
    } catch (_) {
        setServerOnline(false);
        clearOutgoingList(true);
        if (showAlertOnOffline) alertServerOffline();
        else if (status) status.innerText = t("web_server_offline_short");
    }
}

async function downloadFile(url, name) {
    if (!(await requireServerOnline(true))) return;

    const status = document.getElementById("receiveStatus");
    if (status) status.innerText = t("web_downloading") + " " + name;

    try {
        const res = await fetch(url, { cache: "no-store" });
        if (!res.ok) {
            setServerOnline(false);
            alertServerOffline();
            clearOutgoingList(true);
            return;
        }
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(blobUrl);
        if (status) status.innerText = t("web_download_ok");
    } catch (_) {
        setServerOnline(false);
        alertServerOffline();
        clearOutgoingList(true);
    }
}

document.getElementById("fileInput").addEventListener("change", async function () {
    const file = this.files[0];
    const el = document.getElementById("fileName");

    if (!file) {
        if (el) {
            el.textContent = "";
            el.classList.remove("has-file");
        }
        return;
    }

    if (!(await requireServerOnline(true))) {
        this.value = "";
        if (el) {
            el.textContent = "";
            el.classList.remove("has-file");
        }
        return;
    }

    if (el) {
        el.textContent = file.name;
        el.classList.add("has-file");
    }
});

document.getElementById("sendBtn").addEventListener("click", uploadFile);
document.getElementById("refreshBtn").addEventListener("click", () => loadOutgoing(true));

loadAppInfo();
loadI18n().then(() => startHealthPoll());
