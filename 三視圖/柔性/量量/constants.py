SOP_TYPES = {"electrical": "电性", "thermal": "热负载", "process": "製程"}

DELAY_REASONS = {
    "equipment_cooling": "冷卻系统故障",
    "equipment_vna": "VNA/电源异常",
    "equipment_wiring": "线路接触不良",
    "equipment_vacuum": "真空泄漏",
    "sample_bonding": "打线失效",
    "sample_contact": "接触电阻超标",
    "sample_contamination": "样品污染",
    "sample_process": "製程偏差",
    "env_temp": "温度未稳定",
    "env_emi": "电磁干扰",
    "env_vibration": "振动",
    "env_access": "实验室准入延迟",
    "people_unavailable": "负责人不可用",
    "people_conflict": "设备排程冲突",
    "people_prereq": "前置 SOP 未完成",
    "criteria_fail": "判据未通过需重测",
    "criteria_data": "数据质量不足",
    "criteria_calibration": "校准失效",
    "other": "其他",
}

PROCEDURE_STATUS = ["not_started", "in_progress", "completed"]
CRITERIA_STATUS = ["not_executed", "pass", "fail", "conditional"]
ROLES = ["viewer", "executor", "admin"]
DECISION_LABELS = ["决策一", "决策二", "决策三", "决策四", "决策五", "无"]
