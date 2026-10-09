"""竞品方案对比分析助手 —— 数据模型与常量定义。

本项目的领域对象：竞品产品、对比维度、结构化对比单元格、对比报告。
数据结构刻意保持轻量（dataclass + 普通字典），便于离线零依赖运行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# 统一的语义匹配阈值：相似度 >= 该值才认为「需求命中该竞品能力/对比维度」
SEMANTIC_THRESHOLD = 0.55

# 支持的对比维度（业务侧定义，可扩展）
DEFAULT_DIMENSIONS = [
    "产品定位",
    "核心功能",
    "性能指标",
    "价格体系",
    "生态兼容",
    "服务支持",
]

# 竞争定位分档（赢单策略的定性结论）
STRENGTH = "我方优势"
PARITY = "势均力敌"
GAP = "我方短板"


def _dimension_id(dimension: str) -> str:
    """把中文维度名转成稳定 ASCII 键名，供结构化单元格 JSON Schema 使用。"""
    mapping = {
        "产品定位": "positioning",
        "核心功能": "features",
        "性能指标": "performance",
        "价格体系": "pricing",
        "生态兼容": "ecosystem",
        "服务支持": "service",
    }
    return mapping.get(dimension, f"dim_{len(dimension)}")


# 竞争定位分档（每个维度我方相对竞品的强弱）
#   +1 = 我方优势  0 = 势均力敌  -1 = 我方短板
POSITION_STRONG = 1
POSITION_PARITY = 0
POSITION_GAP = -1


@dataclass
class Competitor:
    """一个竞品产品。能力点（capabilities）是语义检索的最小单元。

    positioning : Dict[维度名, int]
        领域竞争定位模型：销售/售前团队平时积累的"我方在该维度相对该竞品的强弱"，
        取值 POSITION_STRONG / POSITION_PARITY / POSITION_GAP。
        这是真实竞品分析里"结论"的来源；相似度则负责召回与对齐、并作为佐证。
    """

    name: str
    category: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    # 结构化的分维度描述，键为维度中文名
    spec: Dict[str, str] = field(default_factory=dict)
    # 分维度竞争定位（我方相对该竞品的强弱），键为维度中文名
    positioning: Dict[str, int] = field(default_factory=dict)


@dataclass
class ComparisionRow:
    """对比表的其中一行（一个维度）。"""

    dimension: str
    ours: str
    theirs: str
    conclusion: str
    evidence: str = ""


@dataclass
class ComparisionReport:
    """结构化对比报告。rows 是维度级对比行，summary 是赢单策略总评。"""

    competitor_name: str
    dimensions_compared: int
    rows: List[ComparisionRow] = field(default_factory=list)
    summary: str = ""
    matched_strong: List[str] = field(default_factory=list)
    matched_gap: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转成纯 dict，用于 JSON/演示输出。"""
        return {
            "competitor_name": self.competitor_name,
            "dimensions_compared": self.dimensions_compared,
            "rows": [
                {
                    "dimension": r.dimension,
                    "ours": r.ours,
                    "theirs": r.theirs,
                    "conclusion": r.conclusion,
                    "evidence": r.evidence,
                }
                for r in self.rows
            ],
            "summary": self.summary,
            "matched_strong": self.matched_strong,
            "matched_gap": self.matched_gap,
        }