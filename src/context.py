"""读取并检查项目领域资料。"""

import json
from pathlib import Path

CONTEXT_REQUIRED = {"domain", "version", "facts", "sample_id"}

POLICY_REQUIRED = {
    "domain",
    "version",
    "principles",
    "age_bands",
    "data_categories",
    "pathways",
    "traceable_events",
    "rule_versioning",
    "human_handoff",
    "educator_view",
    "desensitized_event_material",
}

DATA_CATEGORY_KEYS = {
    "usage_time_window",
    "risk_signal",
    "help_request",
    "guardian_school_authorization",
    "human_care_outcome",
}

PATHWAY_KEYS = {
    "ordinary_emotional_expression",
    "sustained_isolation_tendency",
    "urgent_harm_risk",
}

TRACEABLE_EVENT_KEYS = {
    "guardianship_change",
    "consent_withdrawal",
    "in_out_of_school_account_merge",
    "false_positive_appeal",
    "night_shift_handover",
}


def load_context(path: Path) -> dict:
    """返回字段完整的领域资料。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not CONTEXT_REQUIRED.issubset(data):
        raise ValueError("领域资料缺少必要字段")
    return data


def load_policy(path: Path) -> dict:
    """返回字段完整、内部约束一致的守护策略资料。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    _check_policy(data)
    return data


def _check_policy(data: dict) -> None:
    missing = POLICY_REQUIRED - data.keys()
    if missing:
        raise ValueError(f"守护策略缺少必要字段：{sorted(missing)}")
    if data["domain"] != "minor-ai-safeguarding":
        raise ValueError("守护策略领域标识不匹配")
    if not data["principles"]:
        raise ValueError("守护策略至少包含一条原则")

    _check_age_bands(data["age_bands"])
    _check_data_categories(data["data_categories"])
    _check_pathways(data["pathways"])
    _check_traceable_events(data["traceable_events"])

    if data["rule_versioning"].get("prior_dispositions_frozen") is not True:
        raise ValueError("规则更新必须冻结旧处置，不得回溯改写")
    if data["human_handoff"].get("advance_notice_to_child") is not True:
        raise ValueError("转真人前必须提前告知孩子")
    educator_view = data["educator_view"]
    if (
        educator_view.get("shows_support_actions_only") is not True
        or educator_view.get("no_unverified_diagnosis") is not True
    ):
        raise ValueError("教师侧只能看到支持行动，不得呈现未经核实的诊断")
    material = data["desensitized_event_material"]
    if (
        material.get("used_for_boundary_calibration") is not True
        or material.get("not_used_for_individual_labeling") is not True
    ):
        raise ValueError("脱敏事件资料只能用于边界校准，不得用于个体贴标签")


def _check_age_bands(bands: list) -> None:
    if not bands:
        raise ValueError("至少需要一个年龄段")
    last_max = -1
    for band in bands:
        if band["min_age"] < 0:
            raise ValueError("年龄段起始年龄不能为负")
        max_age = band.get("max_age")
        if max_age is not None and max_age < band["min_age"]:
            raise ValueError(f"年龄段 {band['id']} 上限早于下限")
        if band["min_age"] <= last_max:
            raise ValueError(f"年龄段 {band['id']} 与前一年龄段重叠")
        if max_age is not None:
            last_max = max_age


def _check_data_categories(categories: list) -> None:
    keys = {item["key"] for item in categories}
    if keys != DATA_CATEGORY_KEYS:
        raise ValueError(
            f"数据类别集合不完整：缺少 {sorted(DATA_CATEGORY_KEYS - keys)}，"
            f"多余 {sorted(keys - DATA_CATEGORY_KEYS)}"
        )
    for item in categories:
        if item["retention_days"] < item["raw_content_deleted_after_days"]:
            raise ValueError(
                f"数据类别 {item['key']} 的原始内容删除期限晚于摘要保存期限"
            )


def _check_pathways(pathways: list) -> None:
    keys = {item["key"] for item in pathways}
    if keys != PATHWAY_KEYS:
        raise ValueError(
            f"处置路径集合不完整：缺少 {sorted(PATHWAY_KEYS - keys)}，"
            f"多余 {sorted(keys - PATHWAY_KEYS)}"
        )
    for item in pathways:
        if item["key"] == "urgent_harm_risk" and not item["human_handoff"]:
            raise ValueError("紧急伤害风险路径必须转入真人")


def _check_traceable_events(events: list) -> None:
    keys = {item["key"] for item in events}
    if keys != TRACEABLE_EVENT_KEYS:
        raise ValueError(
            f"可追溯事件集合不完整：缺少 {sorted(TRACEABLE_EVENT_KEYS - keys)}，"
            f"多余 {sorted(keys - TRACEABLE_EVENT_KEYS)}"
        )
