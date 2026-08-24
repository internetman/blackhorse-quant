(function () {
  const STORAGE_KEY = "m2-manual-archive-v1";
  let memoryRecords = {};
  let toastTimer = null;

  const bareCode = (value) => String(value || "").split(".")[0];

  const readRecords = () => {
    try {
      const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    } catch (error) {
      console.warn("M2 archive storage is unavailable; using this tab only", error);
      return memoryRecords;
    }
  };

  const writeRecords = (records) => {
    memoryRecords = records;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
    } catch (error) {
      console.warn("M2 archive storage write failed; using this tab only", error);
    }
    window.dispatchEvent(new CustomEvent("m2archivechange", { detail: { records } }));
  };

  const archive = (item) => {
    const key = bareCode(item?.code);
    if (!key) return null;
    const records = readRecords();
    const record = {
      code: String(item.code || key),
      name: String(item.name || key),
      stage: String(item.stage || item.stageInference || ""),
      archivedAt: new Date().toISOString(),
    };
    records[key] = record;
    writeRecords(records);
    return record;
  };

  const restore = (code) => {
    const key = bareCode(code);
    const records = readRecords();
    const record = records[key] || null;
    if (record) {
      delete records[key];
      writeRecords(records);
    }
    return record;
  };

  const isArchived = (code) => Boolean(readRecords()[bareCode(code)]);
  const list = () => Object.values(readRecords()).sort((a, b) => String(b.archivedAt || "").localeCompare(String(a.archivedAt || "")));
  const count = () => list().length;

  const subscribe = (listener) => {
    const onChange = () => listener(list());
    const onStorage = (event) => {
      if (event.key === STORAGE_KEY) onChange();
    };
    window.addEventListener("m2archivechange", onChange);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("m2archivechange", onChange);
      window.removeEventListener("storage", onStorage);
    };
  };

  const notify = (message, actionLabel, action) => {
    let toast = document.getElementById("m2ArchiveToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "m2ArchiveToast";
      toast.className = "archive-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      toast.innerHTML = '<span></span><button type="button"></button>';
      document.body.appendChild(toast);
    }
    const label = toast.querySelector("span");
    const button = toast.querySelector("button");
    label.textContent = message;
    button.textContent = actionLabel || "";
    button.hidden = !actionLabel || typeof action !== "function";
    button.onclick = () => {
      action?.();
      toast.classList.remove("open");
    };
    window.clearTimeout(toastTimer);
    toast.classList.add("open");
    toastTimer = window.setTimeout(() => toast.classList.remove("open"), 4200);
  };

  window.M2Archive = { archive, restore, isArchived, list, count, subscribe, notify, bareCode };
})();
