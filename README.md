# LS900-ESX-GuineaPig-Biometry

**LS900 ESX Guinea Pig Biometry Analyzer**

**LS900豚鼠眼部生物测量ESX解析工具**

<img src="assets/app_icon.png" alt="LS900 Biometry Analyzer icon" width="128">

这是一个在本机运行的研究工具：批量读取 LENSTAR LS 900 导出的原始 `.esx` 文件，自动估计豚鼠的眼轴长度（AL）、角膜厚度（CCT）、前房深度（AD）、晶体厚度（LT）和视网膜厚度（RT），并导出排版简洁的 Excel 文件。

## Windows 便携版

1. 在 GitHub Releases 下载 `LS900-ESX-GuineaPig-Biometry-v0.1.0-windows-x64.zip`。
2. 完整解压 ZIP；不要只把 EXE 单独复制出来。
3. 双击 `LS900 Biometry Analyzer.exe`，程序会在后台运行并自动打开浏览器。
4. 把一个或多个原始 `.esx` 文件拖入页面，点击“开始分析”。
5. Excel 下载完成后，可从 Windows 右下角托盘退出程序。

便携版不需要安装 Python、Conda 或其他运行环境。当前程序没有商业代码签名，Windows SmartScreen 可能在首次运行时提示“未知发布者”；请只从本仓库的 Release 下载，并用一同发布的 SHA-256 校验文件核对。

页面没有 before/after 选项。导出文件按当前时间命名，使用者可以下载后自行改名。

## 输出规则

- `测量数据`：一只动物一行；OD 在左、OS 在右，中间留两列空白。
- 指标顺序：AL、CCT、AD、LT、RT。
- 晶体质量门未通过时，AD 与 LT 留空，不强行给数值。
- 需要复核或留空的项目写在 `说明` 工作表中。
- RT 目前属于探索性结果，不建议作为未经复核的主要终点。

## 数据与隐私

程序只监听本机地址 `127.0.0.1`。选择的 ESX 文件在本机临时目录中处理，生成 Excel 后临时目录会自动删除；程序不会把数据上传到网络。

## 模型边界

当前内置模型版本为 `guinea-lenstar-v4.0.0-combined-train60-2026-10-06`，针对现有豚鼠数据开发。它不是 LENSTAR 厂商算法，也不是医疗器械软件，不能用于临床诊断。将模型用于其他动物、不同设备、不同固件或明显不同的采集流程前，应重新验证。

锁定后固定测试集共 48 眼：AL MAE 为 0.0295 mm，45/48 眼（93.8%）绝对误差不超过 0.10 mm；CCT MAE 为 2.29 μm。晶体质量门通过且人工参考合理的 29 眼中，LT MAE 为 0.0202 mm。RT 目前仍为探索性结果。

## 从源代码运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_app.py
```

随后访问 `http://127.0.0.1:8765`。

## 构建 Windows 版本

```powershell
.\build_windows.ps1
```

输出位于 `dist/LS900 Biometry Analyzer`，可发布压缩包位于 `release/`。GitHub Actions 也会在推送 `v*` 标签时自动构建 Windows 版本并附加到 Release。

## English summary

LS900 ESX Guinea Pig Biometry Analyzer is a local Windows research tool for batch extraction of guinea-pig ocular biometry from raw Lenstar LS 900 ESX files. It exports AL, CCT, AD, LT and exploratory RT measurements to a two-sheet Excel workbook. Processing occurs locally; selected files are not uploaded to a remote server.

## License

MIT。项目与 Haag-Streit 或 LENSTAR 厂商无隶属、授权或背书关系。
