"""结构化生成模块：把检索 + 匹配结果渲染成"竞品对比表"。

用 guided_json 的思路：先定义输出 JSON Schema（对比表每行的字段契约），
再由生成器逐维度产出符合 Schema 的结构化行。这里由 Mock 实现演示同样的契约，
接真实 LLM 时仅替换 `cell_generator.compare_cell` 的实现即可。
"""

from __future__ import annotations

from typing import Any, Dict, List

from .mock_backend import MockStructuredGenerator, _pick_conclusion_from_position
from .models import (
    ComparisionReport,
    ComparisionRow,
    STRENGTH,
    GAP,
    POSITION_PARITY,
)
from .retrieval import KnowledgeBase

CellGenerator = MockStructuredGenerator

# 输出单元格的 JSON Schema 契约（guided_json 的目标结构）
CELL_SCHEMA = {
    "type": "object",
    "properties": {
        "dimension": {"type": "string", "description": "对比维度名"},
        "ours": {"type": "string", "description": "我方案在该维度的要点"},
        "theirs": {"type": "string", "description": "竞品方案在该维度的要点"},
        "conclusion": {
            "type": "string",
            "enum": ["我方优势", "势均力敌", "我方短板"],
            "description": "竞争定位结论",
        },
        "evidence": {"type": "string", "description": "支撑该结论的证据/依据"},
    },
    "required": ["dimension", "ours", "theirs", "conclusion", "evidence"],
    "additionalProperties": False,
}


class StructuredReportGenerator:
    """对比报告生成器：逐维度组合"我方 vs 竞品"并产出结构化结论。"""

    def __init__(self, kb: KnowledgeBase, cell_generator: CellGenerator | None = None) -> None:
        self._kb = kb
        self._cells = cell_generator or MockStructuredGenerator()

    def build_report(self, our_spec: Dict[str, str], competitor_name: str) -> ComparisionReport:
        """生成一个竞品的完整对比报告。

        对每个业务维度：
        1. 我方 spec 里取我方案描述（缺省则回退检索）；
        2. 从知识库取竞品对应维度描述；
        3. 用语义相似度 + 结构化生成器产出该行结论。

        同时聚合出优势/短板维度的清单，供赢单策略使用。
        """
        comp = self._kb.get(competitor_name)
        if comp is None:
            raise KeyError(f"知识库中不存在竞品：{competitor_name}")

        rows: List[ComparisionRow] = []
        strong: List[str] = []
        gap: List[str] = []

        for dim, theirs_desc in comp.spec.items():
            ours_desc = our_spec.get(dim, "")
            if not ours_desc:
                ours_desc = self._recall_our_dimension(dim, our_spec)
            if not theirs_desc:
                theirs_desc = self._kb.recall_dimension(competitor_name, dim)
            if not ours_desc:
                continue

            # 语义相似度用于对齐召回 + 作为佐证（RAG 检索的体现）
            sim = self._semantic_similarity(ours_desc, theirs_desc)
            # 竞争结论来自领域定位模型（真实销售沉淀），相似度作佐证
            position = comp.positioning.get(dim, POSITION_PARITY)
            cell = self._cells.compare_cell(ours_desc, theirs_desc, sim, position)
            conclusion = cell["conclusion"]
            rows.append(
                ComparisionRow(
                    dimension=dim,
                    ours=cell["ours"],
                    theirs=cell["theirs"],
                    conclusion=conclusion,
                    evidence=cell["evidence"],
                )
            )
            if conclusion == STRENGTH:
                strong.append(dim)
            elif conclusion == GAP:
                gap.append(dim)

        summary = self._cells.generate_summary(
            [r.to_dict() if hasattr(r, "to_dict") else vars(r) for r in rows],
            strong,
            gap,
        )
        return ComparisionReport(
            competitor_name=competitor_name,
            dimensions_compared=len(rows),
            rows=rows,
            summary=summary,
            matched_strong=strong,
            matched_gap=gap,
        )

    def _semantic_similarity(self, a: str, b: str) -> float:
        return self._kb._encoder.similarity(a, b)

    def _recall_our_dimension(self, dim: str, our_spec: Dict[str, str]) -> str:
        """我方某维度缺描述时，从已有 spec 里挑相似度最高的那条兜底。"""
        best, best_score = "", -1.0
        for d, desc in our_spec.items():
            score = self._semantic_similarity(dim, d)
            if score > best_score:
                best, best_score = desc, score
        return best