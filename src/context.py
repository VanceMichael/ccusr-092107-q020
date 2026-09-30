"""读取并检查项目领域资料。"""

import json
from pathlib import Path

REQUIRED = {
    "domain",
    "version",
    "facts",
    "sample_id",
    "collection_principle",
    "collected_data",
    "triage_paths",
    "retention_rules",
    "boundary_materials",
    "traceable_events",
    "safeguards",
}

# 三类风险信号必须各有独立处置路径，不得合并降级。
TRIAGE_PATH_CODES = {"ordinary-emotion", "persistent-isolation", "urgent-harm"}

RETENTION_KEYS = {"raw_content", "necessary_summary", "rule_versions"}


def load_context(path: Path) -> dict:
    """返回字段完整、关键编码齐备的领域资料。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not REQUIRED.issubset(data):
        missing = sorted(REQUIRED - data.keys())
        raise ValueError(f"领域资料缺少必要字段: {missing}")

    triage_codes = {item["code"] for item in data["triage_paths"]}
    if not TRIAGE_PATH_CODES.issubset(triage_codes):
        raise ValueError("三类处置路径（普通情绪/持续孤立/紧急伤害）必须齐备")

    if not RETENTION_KEYS.issubset(data["retention_rules"]):
        raise ValueError("留存规则必须覆盖原始内容、必要摘要与规则版本")

    _assert_unique_codes(data["collected_data"], "收集数据")
    _assert_unique_codes(data["triage_paths"], "处置路径")
    _assert_unique_codes(data["traceable_events"], "可追溯事件")
    _assert_unique_codes(data["safeguards"], "保障措施")

    return data


def _assert_unique_codes(items: list, section: str) -> None:
    codes = [item["code"] for item in items]
    if len(codes) != len(set(codes)):
        raise ValueError(f"{section}中存在重复编码")
