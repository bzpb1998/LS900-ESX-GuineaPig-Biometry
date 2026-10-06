# v0.1.0 — 首个 Windows 公开版本

这是 **LS900 ESX Guinea Pig Biometry Analyzer** 的首个公开研究版本。

## 主要功能

- 批量读取 LENSTAR LS 900 导出的原始 `.esx` 文件。
- 输出豚鼠 OD/OS 的 AL、CCT、AD、LT 和探索性 RT。
- 直接生成含 `测量数据` 与 `说明` 两个工作表的 Excel 文件。
- Windows 便携运行，无需安装 Python 或 Conda。
- 数据仅在本机 `127.0.0.1` 处理，不上传至远程服务器。

## 使用方法

1. 下载 `LS900-ESX-GuineaPig-Biometry-v0.1.0-windows-x64.zip`。
2. 完整解压 ZIP 文件。
3. 双击 `LS900 Biometry Analyzer.exe`。
4. 在自动打开的页面中选择或拖入一个或多个 `.esx` 文件，点击“开始分析”。
5. 保存自动下载的 Excel；使用结束后可从系统托盘或页面按钮退出。

## 验证与边界

- 当前内置模型：`guinea-lenstar-v4.0.0-combined-train60-2026-10-06`。
- 锁定测试集 48 眼：AL MAE 0.0295 mm；45/48 眼绝对误差不超过 0.10 mm。
- CCT MAE 2.29 μm。
- 质量门通过且人工参考合理的 29 眼：LT MAE 0.0202 mm。
- RT 目前仍属探索性结果。

本软件是研究工具，不是 LENSTAR 厂商算法或医疗器械软件，不得用于临床诊断。当前可执行文件未进行商业代码签名，Windows SmartScreen 首次运行时可能显示“未知发布者”。
