# LS900-ESX-GuineaPig-Biometry

**软件 v0.2.1 · 锁定模型 V5 · 原生 Windows 独立窗口**。不再自动打开浏览器，不启动本地 HTTP 服务。V5 的历史评价为回顾性，尚待新动物前瞻性验证；完整结果与限制见 [V5_EXPERIMENTAL.md](docs/V5_EXPERIMENTAL.md)。历史 V4/v0.1.0 保留在 Releases。

**LS900 ESX Guinea Pig Biometry Analyzer**

**LS900豚鼠眼部生物测量ESX解析工具**

<img src="assets/app_icon.png" alt="LS900 Biometry Analyzer icon" width="128">

这是一个在本机运行的研究工具：批量读取 LENSTAR LS 900 导出的原始 `.esx` 文件，自动估计豚鼠的眼轴长度（AL）、角膜厚度（CCT）、前房深度（AD）、晶体厚度（LT）和视网膜厚度（RT），并导出排版简洁的 Excel 文件。

## Windows 便携版

1. 在 [GitHub Releases](https://github.com/bzpb1998/LS900-ESX-GuineaPig-Biometry/releases) 下载 `LS900-ESX-GuineaPig-Biometry-v0.2.1-V5-windows-x64.zip`，不是 Source code 或 Code → Download ZIP。
2. 完整解压 ZIP；不要只把 EXE 单独复制出来。
3. 双击 `LS900 Biometry Analyzer.exe`，直接打开独立软件窗口。
4. 把一个或多个原始 `.esx` 文件拖入页面，点击“开始分析”。
5. 点击“保存 Excel”选择位置；关闭软件窗口即可退出。

便携版不需要安装 Python、Conda 或其他运行环境。当前程序没有商业代码签名，Windows SmartScreen 可能在首次运行时提示“未知发布者”；请只从本仓库的 Release 下载，并用一同发布的 SHA-256 校验文件核对。

没有 before/after 选项。导出文件默认按时间命名，使用者可自行改名。详见[使用说明](docs/USER_GUIDE.md)。

![V5 desktop window](assets/desktop-preview.png)

## 输出规则

- `测量数据`：一只动物一行；OD 在左、OS 在右，中间留两列空白。
- 指标顺序：AL、CCT、AD、LT、RT。
- 晶体质量门未通过时，AD 与 LT 留空，不强行给数值。
- 需要复核或留空的项目写在 `说明` 工作表中。
- RT 目前属于探索性结果，不建议作为未经复核的主要终点。

## 数据与隐私

原生桌面版直接在本机读取文件，不监听端口，不修改 ESX 原件，不上传数据。仅在主动点击 GitHub 文档链接时打开网络页面。旧 Flask 网页入口仅保留为代码兼容方式，不是默认 Windows 入口。

## 模型边界

当前模型为 `guinea-lenstar-v5.0.0-animal-grouped-2026-10-16`，针对现有豚鼠数据开发。它不是 LENSTAR 厂商算法，也不是医疗器械软件，不能用于临床诊断。将模型用于其他动物、不同设备、不同固件或明显不同的采集流程前，应重新验证。

历史 48 眼的 V5 回顾性复核：AL MAE 0.02471 mm，43/48 眼绝对误差 ≤0.05 mm，46/48 眼 ≤0.10 mm。CCT MAE 2.29 μm；人工参考符合预设范围且模型门控通过的 29 眼，LT MAE 0.02023 mm。RT 为探索性结果。这不是诊断准确率，不能把已知历史反馈下的 V5 再称为全新盲法测试。

这 48 眼是测量记录级测试，其中 20 眼的动物在另一时间点出现在训练组；28 眼的动物编号未进入训练。不能将全部 48 眼称为动物级完全独立外部验证。

## 从源代码运行

```powershell
conda env create -f environment.yml
conda activate ls900-biometry-v5
python -m pip install -e . --no-deps --no-build-isolation
ls900-desktop
# 或命令行批量输出：
ls900-biometry --input "D:\data\raw" --output "D:\results\measurements.xlsx"
```

依赖锁定、venv 替代方法、实际验证边界和合成示例见[复现说明](docs/REPRODUCIBILITY.md)。无需为了使用软件安装 Conda；它只面向源码使用者。

## 构建 Windows 版本

```powershell
.\build_windows.ps1
```

输出位于 `dist/LS900 Biometry Analyzer V5`，压缩包位于 `release/`。GitHub Actions 在推送 `v*` 标签时自动构建并附加到 Release。第三方许可及 Qt 源码获取方式见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## English summary

LS900 ESX Guinea Pig Biometry Analyzer is a local Windows research tool for batch extraction of guinea-pig ocular biometry from raw Lenstar LS 900 ESX files. It exports AL, CCT, AD, LT and exploratory RT measurements to a two-sheet Excel workbook. Processing occurs locally; selected files are not uploaded to a remote server.

## License

MIT。项目与 Haag-Streit 或 LENSTAR 厂商无隶属、授权或背书关系。
