const input = document.querySelector("#file-input");
const dropZone = document.querySelector("#drop-zone");
const selection = document.querySelector("#selection");
const fileCount = document.querySelector("#file-count");
const fileList = document.querySelector("#file-list");
const clearButton = document.querySelector("#clear-button");
const analyzeButton = document.querySelector("#analyze-button");
const statusBox = document.querySelector("#status");
const exitButton = document.querySelector("#exit-button");
let selectedFiles = [];

function setFiles(files) {
  selectedFiles = Array.from(files).filter(file => file.name.toLowerCase().endsWith(".esx"));
  selection.hidden = selectedFiles.length === 0;
  analyzeButton.disabled = selectedFiles.length === 0;
  fileCount.textContent = `已选择 ${selectedFiles.length} 个 ESX 文件`;
  fileList.replaceChildren(...selectedFiles.slice(0, 100).map(file => {
    const item = document.createElement("li");
    item.textContent = file.name;
    return item;
  }));
  statusBox.textContent = files.length !== selectedFiles.length ? "已自动忽略非 ESX 文件。" : "";
  statusBox.className = "status";
}

input.addEventListener("change", () => setFiles(input.files));
clearButton.addEventListener("click", () => {
  input.value = "";
  setFiles([]);
});
["dragenter", "dragover"].forEach(name => dropZone.addEventListener(name, event => {
  event.preventDefault();
  dropZone.classList.add("dragging");
}));
["dragleave", "drop"].forEach(name => dropZone.addEventListener(name, event => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
}));
dropZone.addEventListener("drop", event => setFiles(event.dataTransfer.files));

analyzeButton.addEventListener("click", async () => {
  if (!selectedFiles.length) return;
  const form = new FormData();
  selectedFiles.forEach(file => form.append("files", file, file.name));
  analyzeButton.disabled = true;
  analyzeButton.textContent = "正在分析…";
  statusBox.className = "status";
  statusBox.textContent = `正在解析 ${selectedFiles.length} 个文件。文件较多时请耐心等待，不要关闭本页。`;
  try {
    const response = await fetch("/analyze", { method: "POST", body: form });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || `分析失败（${response.status}）`);
    }
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : `LS900_Biometry_${Date.now()}.xlsx`;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    statusBox.className = "status success";
    statusBox.textContent = "分析完成，Excel 已开始下载。";
  } catch (error) {
    statusBox.className = "status error";
    statusBox.textContent = error.message;
  } finally {
    analyzeButton.disabled = selectedFiles.length === 0;
    analyzeButton.textContent = "开始分析";
  }
});

if (exitButton) {
  exitButton.addEventListener("click", async () => {
    exitButton.disabled = true;
    statusBox.className = "status";
    statusBox.textContent = "正在退出程序，可以关闭本页面。";
    try {
      await fetch("/shutdown", { method: "POST" });
    } catch (_) {
      // The local server may stop before the browser receives the response.
    }
  });
}
