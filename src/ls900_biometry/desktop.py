"""Native Qt desktop UI. No browser, HTTP server or network is used."""
from __future__ import annotations

import argparse
from datetime import datetime
from importlib.resources import files
from pathlib import Path
import sys

from PySide6.QtCore import Qt, QThread, Signal, QStandardPaths
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QUrl

from . import __version__
from .analysis import MODEL_SHA256, MODEL_VERSION, load_model
from .batch import AnalysisCancelled, BatchResult, run_batch, save_report

REPO_URL = "https://github.com/bzpb1998/LS900-ESX-GuineaPig-Biometry"
STYLE = """
QWidget {font-family:'Segoe UI','Microsoft YaHei UI';font-size:14px;color:#203D50;}
QMainWindow,QWidget#canvas {background:#F3F6F8;}
QFrame#sidebar {background:#102C40;border:0;}
QLabel#brand {color:#FFFFFF;font-size:20px;font-weight:700;}
QLabel#mutedSide {color:#AFC7D1;font-size:12px;}
QLabel#sideBadge {color:#7FE0D1;font-weight:600;}
QLabel#eyebrow {color:#648393;font-size:12px;font-weight:600;}
QLabel#heading {font-size:28px;font-weight:700;color:#16364A;}
QLabel#subtle {color:#637C8C;font-size:13px;}
QLabel#cardHeading {font-size:18px;font-weight:600;}
QFrame#card {background:#FFFFFF;border:1px solid #DBE5EB;border-radius:14px;}
QFrame#drop {background:#F6FBFA;border:1px dashed #6AAEA6;border-radius:10px;}
QLabel#dropTitle {font-size:16px;font-weight:600;color:#24766F;}
QPushButton {background:white;border:1px solid #CADAE3;border-radius:7px;padding:9px 17px;font-weight:600;min-height:20px;}
QPushButton:hover {background:#EBF4F5;border-color:#8FB9BE;}
QPushButton:disabled {background:#F1F4F6;color:#A1AFB8;border-color:#E2E8EC;}
QPushButton#primary {background:#087F76;color:white;border:1px solid #087F76;}
QPushButton#primary:hover {background:#066F67;}
QPushButton#primary:disabled {background:#AECBC8;border-color:#AECBC8;color:#F6FBFA;}
QPushButton#nav {text-align:left;background:transparent;color:#BAD0DA;border:0;padding:12px 16px;}
QPushButton#nav:checked {background:#23485D;color:white;}
QPushButton#nav:hover {background:#1C3D52;}
QTableWidget {background:white;border:1px solid #E1E9EE;border-radius:6px;gridline-color:#EDF2F5;selection-background-color:#E4F3F0;selection-color:#203D50;}
QHeaderView::section {background:#F5F8FA;color:#617C8C;border:0;border-bottom:1px solid #E1E9EE;padding:8px;text-align:left;font-size:12px;}
QProgressBar {border:0;background:#E6EEF1;border-radius:4px;min-height:8px;max-height:8px;}
QProgressBar::chunk {background:#139D91;border-radius:4px;}
QTextBrowser {background:white;border:0;font-size:14px;}
QScrollArea {border:0;background:transparent;}
"""


class Logo(QWidget):
    def __init__(self, size=64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        payload = files("ls900_biometry").joinpath("assets/logo.svg").read_bytes()
        self.renderer = QSvgRenderer(payload, self)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.renderer.render(painter)


def label(text, kind=None, wrap=False):
    item = QLabel(text)
    if kind:
        item.setObjectName(kind)
    item.setWordWrap(wrap)
    return item


def card():
    item = QFrame()
    item.setObjectName("card")
    layout = QVBoxLayout(item)
    layout.setContentsMargins(24, 21, 24, 21)
    layout.setSpacing(12)
    return item, layout


class Worker(QThread):
    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        try:
            result = run_batch(self.paths, self.progress.emit, self.isInterruptionRequested)
            if self.isInterruptionRequested():
                self.cancelled.emit()
            else:
                self.completed.emit(result)
        except AnalysisCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.paths: list[Path] = []
        self.result: BatchResult | None = None
        self.worker: Worker | None = None
        self.setWindowTitle("LS900 Biometry Analyzer · V5")
        self.setWindowIcon(QIcon(str(files("ls900_biometry").joinpath("assets/logo.svg"))))
        self.resize(1160, 840)
        self.setMinimumSize(980, 720)
        self.setAcceptDrops(True)
        root = QWidget()
        root.setObjectName("canvas")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(208)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(22, 30, 22, 24)
        side.setSpacing(12)
        side.addWidget(Logo(68))
        side.addWidget(label("LS900\nBiometry", "brand"))
        side.addWidget(label("ESX ANALYZER", "mutedSide"))
        side.addSpacing(30)
        self.navigation = []
        for index, title in enumerate(("批量分析", "使用说明", "关于与引用")):
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=index: self.navigate(page))
            side.addWidget(button)
            self.navigation.append(button)
        side.addStretch()
        side.addWidget(label("●  本机离线处理", "sideBadge"))
        side.addWidget(label(f"软件 {__version__}  /  模型 V5", "mutedSide"))
        side.addWidget(label("Guinea-pig research\n非厂家软件 · 非临床用途", "mutedSide"))
        outer.addWidget(sidebar)
        self.pages = QStackedWidget()
        outer.addWidget(self.pages, 1)
        analysis_scroll = QScrollArea()
        analysis_scroll.setWidgetResizable(True)
        analysis_scroll.setWidget(self.build_analysis_page())
        self.pages.addWidget(analysis_scroll)
        self.pages.addWidget(self.document_page("使用说明", self.help_html()))
        self.pages.addWidget(self.document_page("关于与引用", self.about_html()))
        self.navigate(0)

    def build_analysis_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 29, 32, 23)
        layout.setSpacing(15)
        layout.addWidget(label("LENSTAR LS 900  /  GUINEA-PIG RESEARCH", "eyebrow"))
        layout.addWidget(label("批量眼部生物测量", "heading"))
        layout.addWidget(label("导入原始 ESX，使用锁定的 V5 模型分析，直接保存 Excel。", "subtle", True))
        input_card, body = card()
        top = QHBoxLayout()
        top.addWidget(label("01   选择原始数据", "cardHeading"))
        top.addStretch()
        self.count_label = label("0 个文件", "subtle")
        top.addWidget(self.count_label)
        body.addLayout(top)
        drop = QFrame()
        drop.setObjectName("drop")
        drop.setMinimumHeight(132)
        drop_layout = QVBoxLayout(drop)
        drop_layout.setContentsMargins(18, 16, 18, 16)
        drop_layout.setSpacing(8)
        title = label("将 ESX 文件拖入窗口，或点击下方添加", "dropTitle", True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(title)
        caption = label("支持批量文件  ·  不修改原件  ·  数据不上传网络", "subtle")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(caption)
        controls = QHBoxLayout()
        controls.addStretch()
        self.add_button = QPushButton("添加 ESX 文件")
        self.add_button.clicked.connect(self.choose_files)
        controls.addWidget(self.add_button)
        self.folder_button = QPushButton("选择文件夹")
        self.folder_button.clicked.connect(self.choose_folder)
        controls.addWidget(self.folder_button)
        controls.addStretch()
        drop_layout.addLayout(controls)
        body.addWidget(drop)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["文件", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 110)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setFixedHeight(106)
        self.table.setAlternatingRowColors(True)
        body.addWidget(self.table, 1)
        row = QHBoxLayout()
        row.addWidget(label("文件夹仅读取当前层级，不扫描其他目录。", "subtle"))
        row.addStretch()
        self.clear_button = QPushButton("清空列表")
        self.clear_button.clicked.connect(self.clear_files)
        row.addWidget(self.clear_button)
        body.addLayout(row)
        layout.addWidget(input_card, 1)
        output_card, output = card()
        output.addWidget(label("02   分析并保存结果", "cardHeading"))
        output.addWidget(label("AL 眼轴  ·  CCT 角膜厚度  ·  AD 前房深度  ·  LT 晶体厚度\nRT 视网膜厚度为探索性结果；不可测项目不强行补值。", "subtle", True))
        buttons = QHBoxLayout()
        self.analyze_button = QPushButton("开始分析")
        self.analyze_button.setObjectName("primary")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.start_analysis)
        buttons.addWidget(self.analyze_button)
        self.save_button = QPushButton("保存 Excel")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.choose_save)
        buttons.addWidget(self.save_button)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch()
        self.details_button = QPushButton("查看处理说明")
        self.details_button.setVisible(False)
        self.details_button.clicked.connect(self.show_details)
        buttons.addWidget(self.details_button)
        output.addLayout(buttons)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        output.addWidget(self.progress_bar)
        self.status_label = label("准备就绪，请先添加原始 ESX 文件。", "subtle", True)
        output.addWidget(self.status_label)
        layout.addWidget(output_card)
        footer = label("仅供研究使用。V5 尚待新动物前瞻性验证；异常解剖与含混峰位需人工复核。", "subtle", True)
        layout.addWidget(footer)
        return page

    def document_page(self, heading, html):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 34, 32, 28)
        layout.setSpacing(22)
        layout.addWidget(label(heading, "heading"))
        frame, content = card()
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        content.addWidget(browser)
        layout.addWidget(frame, 1)
        return page

    def navigate(self, index):
        self.pages.setCurrentIndex(index)
        for position, button in enumerate(self.navigation):
            button.setChecked(position == index)

    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择未手工调整的原始文件", "", "EyeSuite ESX (*.esx *.ESX)")
        self.add_paths(paths)

    def choose_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "选择原始 ESX 文件夹")
        if directory:
            self.add_paths([directory])

    def add_paths(self, paths):
        if self.busy():
            return
        discovered = []
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                discovered.extend(sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() == ".esx"))
            elif path.is_file() and path.suffix.lower() == ".esx":
                discovered.append(path)
        self.paths = list(dict.fromkeys(self.paths + [p.resolve() for p in discovered]))
        self.result = None
        self.save_button.setEnabled(False)
        self.details_button.setVisible(False)
        self.table.setRowCount(len(self.paths))
        for index, path in enumerate(self.paths):
            name = QTableWidgetItem(path.name)
            name.setToolTip(str(path))
            self.table.setItem(index, 0, name)
            self.table.setItem(index, 1, QTableWidgetItem("待分析"))
        self.count_label.setText(f"{len(self.paths)} 个文件")
        self.analyze_button.setEnabled(bool(self.paths))
        self.progress_bar.setValue(0)
        self.status_label.setText(f"已选择 {len(self.paths)} 个文件，可以开始分析。" if self.paths else "没有找到 ESX 文件。")

    def clear_files(self):
        self.paths = []
        self.add_paths([])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.busy():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

    def set_running(self, running):
        for button in (self.add_button, self.folder_button, self.clear_button):
            button.setEnabled(not running)
        self.analyze_button.setEnabled(not running and bool(self.paths))
        self.cancel_button.setVisible(running)

    def start_analysis(self):
        if self.busy() or not self.paths:
            return
        self.result = None
        self.save_button.setEnabled(False)
        self.details_button.setVisible(False)
        self.progress_bar.setRange(0, len(self.paths))
        self.progress_bar.setValue(0)
        self.status_label.setText("正在检查 V5 模型并分析原始信号…")
        self.set_running(True)
        self.worker = Worker(self.paths, self)
        self.worker.progress.connect(self.on_progress)
        self.worker.completed.connect(self.on_completed)
        self.worker.failed.connect(self.on_failed)
        self.worker.cancelled.connect(self.on_cancelled)
        self.worker.finished.connect(lambda: self.set_running(False))
        self.worker.start()

    def on_progress(self, current, total, name):
        self.progress_bar.setValue(current)
        self.table.setItem(current - 1, 1, QTableWidgetItem("已处理"))
        self.status_label.setText(f"已处理 {current}/{total}：{name}")

    def on_completed(self, result):
        self.result = result
        failed_names = {line.split("：", 1)[0] for line in result.errors}
        for index, path in enumerate(self.paths):
            self.table.setItem(index, 1, QTableWidgetItem("需查看说明" if path.name in failed_names else "分析完成"))
        self.save_button.setEnabled(result.usable_eyes > 0)
        self.details_button.setVisible(bool(result.errors))
        self.status_label.setText(f"完成：{result.completed}/{result.total} 个文件，{result.usable_eyes} 眼有 AL 结果。" +
                                  ("请保存 Excel，并查看其中的说明页。" if result.usable_eyes else "没有可导出的眼轴结果。"))

    def on_failed(self, message):
        self.status_label.setText("分析失败：" + message)

    def cancel_analysis(self):
        if self.worker:
            self.worker.requestInterruption()
            self.status_label.setText("正在取消，将在当前文件处理完后停止。")

    def on_cancelled(self):
        self.result = None
        self.status_label.setText("分析已取消；原始文件未修改，未导出不完整结果。")

    def choose_save(self):
        if not self.result:
            return
        directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        name = "LS900_Biometry_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"
        output, _ = QFileDialog.getSaveFileName(self, "保存测量结果", str(Path(directory) / name), "Excel (*.xlsx)")
        if not output:
            return
        if not output.lower().endswith(".xlsx"):
            output += ".xlsx"
            if Path(output).exists() and QMessageBox.question(self, "文件已存在", "是否替换已有的 Excel？") != QMessageBox.StandardButton.Yes:
                return
        try:
            target = save_report(self.result, output)
            self.status_label.setText(f"已保存：{target.name}。测量数据和说明位于同一 Excel 中。")
        except Exception as exc:
            QMessageBox.warning(self, "保存失败", str(exc))

    def show_details(self):
        if self.result:
            dialog = QDialog(self)
            dialog.setWindowTitle("文件处理说明")
            dialog.resize(720, 400)
            layout = QVBoxLayout(dialog)
            text = QTextBrowser()
            text.setPlainText("\n\n".join(self.result.errors))
            layout.addWidget(text)
            dialog.exec()

    def closeEvent(self, event):
        if self.busy():
            self.cancel_analysis()
            self.status_label.setText("正在停止分析，请稍后再次关闭窗口。")
            event.ignore()
        else:
            event.accept()

    @staticmethod
    def help_html():
        return """<h2>三个步骤即可得到结果</h2>
        <p><b>1　添加原始数据。</b>选择或拖入 LENSTAR LS 900 / EyeSuite 导出的 .esx 文件，可批量添加。优先使用未手工调整的原始文件；程序不会改写原件。选择文件夹时只读取当前层。</p>
        <p><b>2　开始分析。</b>同一套 V5 算法处理所有文件。没有 before/after 选项，不进行造模分组或增长统计。</p>
        <p><b>3　保存 Excel。</b>结果一只动物一行，右眼 OD 在左、左眼 OS 在右，中间两列留空。仅有“测量数据”和“说明”两张表，文件名可自行修改。</p>
        <h3>指标与单位</h3><p>AL：角膜前表面至 ILM 的 EyeSuite 等效眼轴长度（mm）。<br>
        CCT：中央角膜厚度（μm）。<br>AD：角膜后表面至晶体前表面的房水深度（mm），不是从角膜前表面起算的 ACD。<br>
        LT：晶体厚度（mm）。<br>RT：视网膜厚度（μm），当前仅供探索性参考。</p>
        <h3>缺失与复核</h3><p>晶体边界不可靠时 AD/LT 留空，不按正常范围猜测数值。眼轴建议复核时保留数值并在说明页提示；质量标签不是准确概率。视网膜脱离等异常解剖不能按正常眼自动判读。</p>
        <h3>数据安全</h3><p>分析完全在本机完成，不启动浏览器或本地服务器，不上传文件。关闭窗口即可退出。软件需要完整解压后运行，不要只移动 EXE。</p>"""

    @staticmethod
    def about_html():
        return f"""<h2>LS900 ESX Guinea Pig Biometry Analyzer</h2>
        <p>LS900 豚鼠眼部生物测量 ESX 解析工具</p>
        <p><b>软件版本：</b>{__version__}　<b>分析模型：</b>V5（固定参数，不在线训练）</p>
        <p><b>模型标识：</b>{MODEL_VERSION}<br><b>模型 SHA-256：</b><br>{MODEL_SHA256}</p>
        <h3>研究范围与局限</h3><p>用于复现人工拖峰后的 EyeSuite 等效测量，不等同于经过独立解剖学标定的真实几何尺寸。V5 的历史评价为回顾性，尚待新动物前瞻性验证；部分眼存在错层风险，RT 仅供探索。</p>
        <p>本工具独立于 Haag-Streit / LENSTAR 厂家，未经厂家背书，不是医疗器械软件，不得用于临床诊断。</p>
        <h3>开源与引用</h3><p>作者：Junbiao Zhang。项目源码采用 MIT；Qt/PySide6 等第三方许可见发布包 THIRD_PARTY_NOTICES。论文 DOI 尚未分配，不虚构引用。</p>
        <p>引用建议：Zhang J. LS900 ESX Guinea Pig Biometry Analyzer, software {__version__}, model V5 (2026). GitHub repository.</p>
        <p><a href="{REPO_URL}">打开 GitHub 源代码与文档（需要联网）</a></p>"""


def main():
    parser = argparse.ArgumentParser(description="LS900 native desktop analyzer")
    parser.add_argument("--screenshot", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("LS900 Biometry Analyzer")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    load_model()
    window = MainWindow()
    window.show()
    if args.screenshot:
        from PySide6.QtCore import QTimer
        def snapshot():
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(args.screenshot))
            app.quit()
        QTimer.singleShot(800, snapshot)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
