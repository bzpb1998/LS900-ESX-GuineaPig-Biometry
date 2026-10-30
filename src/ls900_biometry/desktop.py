"""Native Qt desktop UI. No browser, HTTP server or network is used."""
from __future__ import annotations

import argparse
from datetime import datetime
from importlib.resources import files
from pathlib import Path
import sys

from PySide6.QtCore import Qt, QThread, Signal, QStandardPaths, QRectF
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QUrl

from . import __version__
from .analysis import MODEL_SHA256, MODEL_VERSION, load_model
from .branding import APP_NAME, APP_TAGLINE, PROJECT_NOTICE, REPO_URL
from .batch import AnalysisCancelled, BatchResult, run_batch, save_report

STYLE = """
QWidget {font-family:'Segoe UI','Microsoft YaHei UI';font-size:12px;color:#26292E;}
QMainWindow,QWidget#canvas,QWidget#page {background:#F7F8FA;}
QFrame#topbar {background:#FFFFFF;border-bottom:1px solid #E9EAEE;}
QLabel#brand {color:#20242B;font-size:14px;font-weight:600;}
QLabel#brandSub {color:#9297A1;font-size:11px;}
QLabel#heading {font-size:20px;font-weight:600;color:#20242B;}
QLabel#subtle {color:#747C89;font-size:11px;}
QLabel#cardHeading {font-size:14px;font-weight:600;color:#30343B;}
QLabel#step {color:#9399A5;font-size:11px;font-weight:400;}
QLabel#dropTitle {font-size:14px;font-weight:500;color:#363B44;}
QLabel#localStatus {color:#587F6B;font-size:11px;}
QLabel#status {font-size:12px;font-weight:500;color:#333A44;}
QFrame#card {background:#FFFFFF;border:1px solid #E4E7EC;border-radius:9px;}
QFrame#drop {background:#FAFBFD;border:1px dashed #C7CFDC;border-radius:7px;}
QFrame#iconShell {background:#EDF2FA;border:1px solid #E4EAF5;border-radius:8px;}
QFrame#actionBar {background:#FFFFFF;border-top:1px solid #ECEEF2;}
QPushButton {background:#FFFFFF;border:1px solid #DCE0E7;border-radius:5px;padding:7px 14px;font-weight:500;min-height:18px;color:#4D535E;}
QPushButton:hover {background:#F5F7FB;border-color:#B9C3D5;}
QPushButton:focus {border:1px solid #4879D8;}
QPushButton:disabled {background:#F3F4F6;color:#B1B5BD;border-color:#EBECEF;}
QPushButton#primary {background:#3568C8;color:#FFFFFF;border:1px solid #3568C8;padding:8px 19px;}
QPushButton#primary:hover {background:#2D5BB4;border-color:#2D5BB4;}
QPushButton#primary:disabled {background:#E4E8F0;border-color:#E4E8F0;color:#A1AABA;}
QPushButton#quiet {background:transparent;border-color:transparent;color:#7D8490;}
QPushButton#quiet:hover {background:#F1F3F7;color:#3568C8;}
QPushButton#quiet:disabled {background:transparent;color:#C2C6CD;}
QPushButton#nav {text-align:center;background:transparent;color:#7D8390;border:0;border-bottom:2px solid transparent;border-radius:0;padding:10px 4px 8px;font-weight:400;}
QPushButton#nav:checked {color:#2E5EAD;border-bottom:2px solid #4676D1;}
QPushButton#nav:hover {color:#3568C8;}
QTableWidget {background:#FFFFFF;alternate-background-color:#FAFBFC;border:0;border-top:1px solid #ECEEF2;gridline-color:#F0F1F4;selection-background-color:#EBF1FC;selection-color:#30343B;}
QTableWidget::item {padding:4px 9px;border-bottom:1px solid #F2F3F5;}
QHeaderView::section {background:#FAFBFC;color:#969BA5;border:0;border-bottom:1px solid #ECEEF2;padding:9px;text-align:left;font-size:10px;font-weight:400;}
QProgressBar {border:0;background:#EBEDF2;border-radius:2px;min-height:4px;max-height:4px;}
QProgressBar::chunk {background:#4879D8;border-radius:2px;}
QTextBrowser {background:#FFFFFF;border:0;font-size:13px;color:#505661;}
QScrollArea {border:0;background:transparent;}
QScrollBar:vertical {background:transparent;width:8px;margin:2px;}
QScrollBar::handle:vertical {background:#D3D8E1;min-height:24px;border-radius:3px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
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


class Glyph(QWidget):
    """Small, consistent line icons; no platform-dependent icon fonts."""
    def __init__(self, name, size=20, color="#52735E", parent=None):
        super().__init__(parent)
        self.name = name
        self.color = QColor(color)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.scale(self.width() / 24, self.height() / 24)
        path = QPainterPath()
        if self.name == "upload":
            path.moveTo(12, 16); path.lineTo(12, 4)
            path.moveTo(7.5, 8.5); path.lineTo(12, 4); path.lineTo(16.5, 8.5)
            path.moveTo(5, 14); path.lineTo(5, 19); path.lineTo(19, 19); path.lineTo(19, 14)
        elif self.name == "file":
            path.moveTo(6, 3); path.lineTo(14, 3); path.lineTo(18, 7); path.lineTo(18, 21); path.lineTo(6, 21); path.closeSubpath()
            path.moveTo(14, 3); path.lineTo(14, 7); path.lineTo(18, 7)
            path.moveTo(9, 12); path.lineTo(15, 12); path.moveTo(9, 16); path.lineTo(15, 16)
        elif self.name == "check":
            path.moveTo(5, 12.5); path.lineTo(10, 17); path.lineTo(19, 7)
        elif self.name == "shield":
            path.moveTo(12, 3); path.lineTo(19, 6); path.lineTo(19, 12)
            path.cubicTo(19, 17, 15, 20, 12, 21)
            path.cubicTo(9, 20, 5, 17, 5, 12); path.lineTo(5, 6); path.closeSubpath()
            path.moveTo(8.5, 12); path.lineTo(11, 14.5); path.lineTo(16, 9.5)
        elif self.name == "arrow":
            path.moveTo(4, 12); path.lineTo(19, 12); path.moveTo(14, 7); path.lineTo(19, 12); path.lineTo(14, 17)
        elif self.name == "chart":
            path.moveTo(4, 20); path.lineTo(4, 4); path.moveTo(4, 20); path.lineTo(20, 20)
            path.moveTo(7, 16); path.lineTo(11, 11); path.lineTo(14, 14); path.lineTo(20, 6)
        elif self.name == "book":
            path.moveTo(12, 6); path.cubicTo(9, 4, 5, 4, 3, 5); path.lineTo(3, 19); path.cubicTo(6, 18, 9, 18, 12, 20)
            path.cubicTo(15, 18, 18, 18, 21, 19); path.lineTo(21, 5); path.cubicTo(19, 4, 15, 4, 12, 6); path.lineTo(12, 20)
        else:
            painter.drawEllipse(QRectF(4, 4, 16, 16))
            path.moveTo(12, 11); path.lineTo(12, 17); path.moveTo(12, 7); path.lineTo(12, 7.2)
        painter.drawPath(path)


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
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(files("ls900_biometry").joinpath("assets/logo.svg"))))
        self.resize(820, 630)
        self.setMinimumSize(700, 530)
        self.setAcceptDrops(True)
        root = QWidget()
        root.setObjectName("canvas")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(58)
        top = QHBoxLayout(topbar)
        top.setContentsMargins(27, 0, 27, 0)
        top.setSpacing(12)
        top.addWidget(Logo(30))
        top.addWidget(label(APP_NAME, "brand"))
        top.addWidget(label(APP_TAGLINE, "brandSub"))
        top.addStretch()
        self.navigation = []
        for index, title in enumerate(("工作台", "使用说明", "关于")):
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=index: self.navigate(page))
            top.addWidget(button)
            self.navigation.append(button)
        outer.addWidget(topbar)
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
        page.setObjectName("page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 25, 30, 18)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label("眼部生物测量", "heading"))
        header.addStretch()
        header.addWidget(label("●  本机处理", "localStatus"))
        layout.addLayout(header)
        layout.addWidget(label("批量读取原始信号，生成左右眼测量表。", "subtle", True))
        layout.addSpacing(3)
        input_card, body = card()
        body.setContentsMargins(20, 18, 20, 0)
        body.setSpacing(12)
        top = QHBoxLayout()
        top.addWidget(label("原始数据", "cardHeading"))
        self.count_label = label("0 个文件", "subtle")
        top.addWidget(self.count_label)
        top.addStretch()
        self.clear_button = QPushButton("清空列表")
        self.clear_button.setObjectName("quiet")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_files)
        top.addWidget(self.clear_button)
        body.addLayout(top)
        drop = QFrame()
        drop.setObjectName("drop")
        drop.setMinimumHeight(92)
        drop_layout = QHBoxLayout(drop)
        drop_layout.setContentsMargins(16, 14, 16, 14)
        drop_layout.setSpacing(14)
        icon_frame = QFrame()
        icon_frame.setObjectName("iconShell")
        icon_frame.setFixedSize(42, 42)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(10, 10, 10, 10)
        icon_layout.addWidget(Glyph("upload", 20, "#6580B2"))
        drop_layout.addWidget(icon_frame)
        drop_text = QVBoxLayout()
        drop_text.setSpacing(5)
        drop_text.addWidget(label("拖入 ESX 文件", "dropTitle"))
        drop_text.addWidget(label("支持多文件或文件夹批量导入", "subtle", True))
        drop_layout.addLayout(drop_text, 1)
        self.add_button = QPushButton("选择文件")
        self.add_button.clicked.connect(self.choose_files)
        drop_layout.addWidget(self.add_button)
        self.folder_button = QPushButton("选择文件夹")
        self.folder_button.clicked.connect(self.choose_folder)
        drop_layout.addWidget(self.folder_button)
        body.addWidget(drop)
        self.empty_state = QFrame()
        self.empty_state.setMinimumHeight(110)
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(0, 12, 0, 12)
        empty_layout.setSpacing(10)
        empty_layout.addStretch()
        empty_icon = QHBoxLayout()
        empty_icon.addStretch()
        empty_icon.addWidget(Glyph("file", 24, "#AAB4C5"))
        empty_icon.addStretch()
        empty_layout.addLayout(empty_icon)
        empty_text = label("尚未添加文件", "subtle")
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_text)
        empty_layout.addStretch()
        body.addWidget(self.empty_state, 1)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["原始文件", "处理状态"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.setColumnWidth(1, 110)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(110)
        self.table.verticalHeader().setDefaultSectionSize(37)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setVisible(False)
        body.addWidget(self.table, 1)
        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action = QHBoxLayout(action_bar)
        action.setContentsMargins(0, 15, 0, 15)
        action.setSpacing(9)
        status_area = QVBoxLayout()
        status_area.setSpacing(6)
        self.status_label = label("请先添加原始 ESX 文件", "status", True)
        status_area.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        status_area.addWidget(self.progress_bar)
        action.addLayout(status_area, 1)
        self.details_button = QPushButton("查看处理说明")
        self.details_button.setObjectName("quiet")
        self.details_button.setVisible(False)
        self.details_button.clicked.connect(self.show_details)
        action.addWidget(self.details_button)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        action.addWidget(self.cancel_button)
        self.analyze_button = QPushButton("开始分析")
        self.analyze_button.setObjectName("primary")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.start_analysis)
        action.addWidget(self.analyze_button)
        self.save_button = QPushButton("保存 Excel")
        self.save_button.setObjectName("primary")
        self.save_button.setEnabled(False)
        self.save_button.setVisible(False)
        self.save_button.clicked.connect(self.choose_save)
        action.addWidget(self.save_button)
        body.addWidget(action_bar)
        layout.addWidget(input_card, 1)
        footer = label("独立科研工具（非厂家产品）  ·  文件夹仅读取当前层级  ·  异常峰位请人工复核", "subtle", True)
        layout.addWidget(footer)
        return page

    def document_page(self, heading, html):
        page = QWidget()
        page.setObjectName("page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 25, 30, 24)
        layout.setSpacing(16)
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
        if paths:
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
        if not discovered:
            self.status_label.setText("没有找到 ESX 文件；请选择文件或检查文件夹。")
            return
        new_paths = list(dict.fromkeys(self.paths + [p.resolve() for p in discovered]))
        if len(new_paths) == len(self.paths):
            self.status_label.setText("所选文件已在列表中。")
            return
        self.paths = new_paths
        self.refresh_paths()

    def refresh_paths(self):
        self.result = None
        self.save_button.setEnabled(False)
        self.save_button.setVisible(False)
        self.analyze_button.setVisible(True)
        self.analyze_button.setText("开始分析")
        self.details_button.setVisible(False)
        self.empty_state.setVisible(not self.paths)
        self.table.setVisible(bool(self.paths))
        self.table.setRowCount(len(self.paths))
        for index, path in enumerate(self.paths):
            name = QTableWidgetItem(path.name)
            name.setToolTip(str(path))
            self.table.setItem(index, 0, name)
            self.table.setItem(index, 1, QTableWidgetItem("待分析"))
        self.count_label.setText(f"{len(self.paths)} 个文件")
        self.analyze_button.setEnabled(bool(self.paths))
        self.clear_button.setEnabled(bool(self.paths))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"已添加 {len(self.paths)} 个文件，可以开始分析。" if self.paths else "请先添加原始 ESX 文件")

    def clear_files(self):
        if self.busy():
            return
        self.paths = []
        self.refresh_paths()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.busy():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

    def set_running(self, running):
        for button in (self.add_button, self.folder_button):
            button.setEnabled(not running)
        self.clear_button.setEnabled(not running and bool(self.paths))
        self.analyze_button.setEnabled(not running and bool(self.paths))
        self.cancel_button.setVisible(running)
        self.progress_bar.setVisible(running)

    def start_analysis(self):
        if self.busy() or not self.paths:
            return
        self.result = None
        self.save_button.setEnabled(False)
        self.save_button.setVisible(False)
        self.analyze_button.setVisible(True)
        self.details_button.setVisible(False)
        self.progress_bar.setRange(0, len(self.paths))
        self.progress_bar.setValue(0)
        for index in range(len(self.paths)):
            self.table.setItem(index, 1, QTableWidgetItem("待分析"))
        self.status_label.setText("正在分析原始信号…")
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
            failed = path.name in failed_names
            status = QTableWidgetItem("需查看说明" if failed else "分析完成")
            status.setForeground(QColor("#A56729" if failed else "#388164"))
            self.table.setItem(index, 1, status)
        self.save_button.setEnabled(result.usable_eyes > 0)
        self.save_button.setVisible(result.usable_eyes > 0)
        self.analyze_button.setVisible(not result.usable_eyes)
        self.analyze_button.setText("重新分析")
        self.details_button.setVisible(bool(result.errors))
        self.status_label.setText(f"分析完成：{result.completed}/{result.total} 个文件，{result.usable_eyes} 眼有 AL 结果。" +
                                  ("请保存后查看说明页。" if result.usable_eyes else "没有可导出的眼轴结果。"))

    def on_failed(self, message):
        self.analyze_button.setText("重新分析")
        self.status_label.setText("分析失败：" + message)

    def cancel_analysis(self):
        if self.worker:
            self.worker.requestInterruption()
            self.status_label.setText("正在取消，将在当前文件处理完后停止。")

    def on_cancelled(self):
        self.result = None
        self.analyze_button.setText("重新分析")
        self.status_label.setText("分析已取消；原始文件未修改，未导出不完整结果。")

    def choose_save(self):
        if not self.result:
            return
        directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        name = APP_NAME + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx"
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
        <p><b>2　开始分析。</b>程序使用固定算法处理所有文件。没有 before/after 选项，不进行造模分组或增长统计。</p>
        <p><b>3　保存 Excel。</b>结果一只动物一行，右眼 OD 在左、左眼 OS 在右，中间两列留空。仅有“测量数据”和“说明”两张表，文件名可自行修改。</p>
        <h3>指标与单位</h3><p>AL：角膜前表面至 ILM 的 EyeSuite 等效眼轴长度（mm）。<br>
        CCT：中央角膜厚度（μm）。<br>AD：角膜后表面至晶体前表面的房水深度（mm），不是从角膜前表面起算的 ACD。<br>
        LT：晶体厚度（mm）。<br>RT：视网膜厚度（μm），当前仅供探索性参考。</p>
        <h3>缺失与复核</h3><p>晶体边界不可靠时 AD/LT 留空，不按正常范围猜测数值。眼轴建议复核时保留数值并在说明页提示；质量标签不是准确概率。视网膜脱离等异常解剖不能按正常眼自动判读。</p>
        <h3>数据安全</h3><p>分析完全在本机完成，不启动浏览器或本地服务器，不上传文件。关闭窗口即可退出。软件需要完整解压后运行，不要只移动 EXE。</p>"""

    @staticmethod
    def about_html():
        return f"""<h2>{APP_NAME}</h2>
        <p>{APP_TAGLINE} · 眼部生物测量研究工具</p>
        <p><b>软件版本：</b>{__version__}　<b>分析模型：</b>固定参数，不在线训练</p>
        <p><b>模型标识：</b>{MODEL_VERSION}<br><b>模型 SHA-256：</b><br>{MODEL_SHA256}</p>
        <h3>研究范围与局限</h3><p>用于复现人工拖峰后的 EyeSuite 等效测量，不等同于经过独立解剖学标定的真实几何尺寸。现有评价为回顾性，尚待新动物前瞻性验证；部分眼存在错层风险，RT 仅供探索。</p>
        <p>{PROJECT_NOTICE} 仅供科研，不得用于临床诊断。</p>
        <p>本程序只读取使用者提供的 ESX，不连接或修改仪器数据库。软件按现状提供，不保证准确性或适用性；适用法律允许范围内的责任限制见随附 MIT LICENSE。使用者须保存原始备份并复核研究结果。</p>
        <h3>开源与引用</h3><p>作者：Junbiao Zhang。项目源码采用 MIT；Qt/PySide6 等第三方许可见发布包 THIRD_PARTY_NOTICES。论文 DOI 尚未分配，不虚构引用。</p>
        <p>引用建议：Zhang J. OcularSpan. 正式发表时请注明使用的软件发布版本。</p>
        <p><a href="{REPO_URL}">打开 GitHub 源代码与文档（需要联网）</a></p>"""


def main():
    parser = argparse.ArgumentParser(description="OcularSpan native desktop research tool")
    parser.add_argument("--screenshot", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
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
