"""One batch service shared by the command line and native desktop window."""
from dataclasses import dataclass, field
from datetime import datetime
import math
import os
from pathlib import Path
import tempfile
from typing import Callable, Iterable

from .analysis import MODEL_SHA256, MODEL_VERSION, analyze_esx
from .exporter import export_report


@dataclass
class BatchResult:
    rows: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    completed: int = 0
    total: int = 0

    @property
    def usable_eyes(self) -> int:
        return sum(math.isfinite(float(row.get("predicted_AL_mm", math.nan))) for row in self.rows)


class AnalysisCancelled(Exception):
    pass


def run_batch(paths: Iterable[Path], progress: Callable | None = None,
              cancelled: Callable[[], bool] | None = None) -> BatchResult:
    unique = list(dict.fromkeys(Path(path).resolve() for path in paths))
    result = BatchResult(total=len(unique))
    for index, path in enumerate(unique, 1):
        if cancelled and cancelled():
            raise AnalysisCancelled("分析已取消，未导出不完整结果。")
        try:
            if path.suffix.lower() != ".esx":
                raise ValueError("仅支持 .esx 文件")
            rows = analyze_esx(path)
            if not rows:
                raise ValueError("没有有效的眼别测量记录")
            result.rows.extend(rows)
            if any(math.isfinite(float(row.get("predicted_AL_mm", math.nan))) for row in rows):
                result.completed += 1
            else:
                result.errors.append(f"{path.name}：眼部数据处理失败，请查看说明页。")
        except Exception as exc:
            # One malformed input must not discard other valid files.
            result.errors.append(f"{path.name}：{exc}")
        if progress:
            progress(index, result.total, path.name)
    return result


def save_report(result: BatchResult, output: str | Path) -> Path:
    if not result.usable_eyes:
        raise ValueError("没有成功计算的眼轴结果，不能导出测量表。")
    target = Path(output)
    if target.suffix.lower() != ".xlsx":
        raise ValueError("输出文件必须为 .xlsx")
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".ls900_", suffix=".xlsx", dir=target.parent)
    os.close(handle)
    temporary = Path(temp_name)
    try:
        export_report(result.rows, temporary,
                      title="LS900_Biometry_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                      extra_notes=[
                          "V5 的现有评价为回顾性，尚待新动物前瞻性验证；仅供豚鼠研究。",
                          "质量标记为启发式判断，不是准确概率；异常解剖与含混峰位须复核。",
                          "模型 SHA-256：" + MODEL_SHA256,
                      ], file_errors=result.errors)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target
