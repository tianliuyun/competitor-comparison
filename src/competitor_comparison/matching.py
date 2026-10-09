"""语义匹配模块：需求 → 竞品能力的对齐。

职责：
- 语义相似度打分（BiEncoder 余弦，换真后端零改动）
- 基于阈值（见 models.SEMANTIC_THRESHOLD）判定"需求命中"并输出命中结论
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .mock_backend import MockBiEncoder
from .models import Competitor, SEMANTIC_THRESHOLD
from .retrieval import KnowledgeBase

EmbeddingBackend = MockBiEncoder


@dataclass
class Match:
    """一次需求 → 竞品能力 的语义对齐结果。"""

    competitor: str
    capability: str
    dimension: str  # 归到的业务维度
    similarity: float
    matched: bool  # 是否超过阈值

    def to_dict(self) -> Dict[str, Any]:
        return {
            "competitor": self.competitor,
            "capability": self.capability,
            "dimension": self.dimension,
            "similarity": round(self.similarity, 4),
            "matched": self.matched,
        }


class SemanticMatcher:
    """语义匹配引擎：把需求文本对齐到各竞品的能力点，并给出是否"命中"的判定。"""

    def __init__(self, kb: KnowledgeBase) -> None:
        self._kb = kb
        self._encoder = kb._encoder

    def match_query(self, query: str, competitor: str | None = None, top_k: int = 5) -> List[Match]:
        """对需求文本逐竞品打分，返回按相似度降序的对齐结果。

        Parameters
        ----------
        competitor : 若不指定则对知识库里全部竞品打分。
        """
        comps = self._kb.competitors if competitor is None else [self._kb.get(competitor)]
        comps = [c for c in comps if c is not None]
        results: List[Match] = []
        for comp in comps:
            for cap in comp.capabilities:
                sim = self._encoder.similarity(query, cap)
                dim = self._assign_dimension(cap)
                results.append(
                    Match(
                        competitor=comp.name,
                        capability=cap,
                        dimension=dim,
                        similarity=sim,
                        matched=sim >= SEMANTIC_THRESHOLD,
                    )
                )
        # 优先展示命中项，其次按相似度降序
        results.sort(key=lambda m: (-m.matched, -m.similarity))
        return results[:top_k]

    def is_satisfied(self, query: str, competitor: str) -> bool:
        """判断竞品是否已能覆盖该需求（存在任一命中能力点）。"""
        return any(m.matched for m in self.match_query(query, competitor=competitor, top_k=10))

    def _assign_dimension(self, text: str) -> str:
        from .mock_backend import _CONCEPT_LEXICON

        for dim, syns in _CONCEPT_LEXICON.items():
            for syn in syns:
                if syn in text:
                    return dim
        return "其他"