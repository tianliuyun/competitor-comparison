"""RAG 检索模块：对竞品知识库做召回。

两种召回方式：
1. `recall_by_query(query, top_k)`：把需求文本对整个知识库打分，返回最相关的 Top-K 竞品能力点
   —— 对应「客户需求 → 自动对标最相关的竞品功能点」。
2. `recall_dimension(competitor, dimension)`：按业务维度精确取结构化的分维度描述
   —— 对应「对比表按维度逐行填充」。

这里的打分核心 `score(query, text)` 直接使用语义编码器的余弦相似度，
换真实 embedding 后端时无需改动上层。纯内存实现，离线可用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .mock_backend import MockStructuredGenerator
from .mock_backend import MockBiEncoder
from .models import Competitor, SEMANTIC_THRESHOLD

EmbeddingBackend = MockBiEncoder


@dataclass
class Hit:
    """一次检索命中的结果。"""

    competitor: str
    capability: str
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "competitor": self.competitor,
            "capability": self.capability,
            "score": round(self.score, 4),
        }


class VectorIndex:
    """把所有能力点扁平化建成一个向量索引（内存版 FAISS）。"""

    def __init__(self, items: List[Competitor], encoder: EmbeddingBackend) -> None:
        self._items: List[tuple] = []  # (competitor, capability_text)
        self._vecs: List[List[float]] = []
        self._encoder = encoder
        for comp in items:
            for cap in comp.capabilities:
                self._items.append((comp.name, cap))
                self._vecs.append(encoder.encode(cap))

    def search(self, query: str, top_k: int) -> List[Hit]:
        qv = self._encoder.encode(query)
        scored = []
        for (comp, cap), vec in zip(self._items, self._vecs):
            score = _cos(vec, qv)
            if score >= SEMANTIC_THRESHOLD:
                scored.append(Hit(comp, cap, score))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]


def _cos(a: List[float], b: List[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


class KnowledgeBase:
    """竞品知识库：管理竞品集合 + 构建向量索引 + 提供维度级结构化查询。"""

    def __init__(self, items: List[Competitor], encoder: EmbeddingBackend | None = None) -> None:
        self._items = list(items)
        self._by_name = {c.name: c for c in self._items}
        self._encoder = encoder or MockBiEncoder()
        self._index = VectorIndex(self._items, self._encoder)

    @property
    def competitors(self) -> List[Competitor]:
        return self._items

    def get(self, name: str) -> Competitor | None:
        return self._by_name.get(name)

    def recall_by_query(self, query: str, top_k: int = 3) -> List[Hit]:
        return self._index.search(query, top_k)

    def recall_dimension(self, competitor: str, dimension: str) -> str:
        """按维度取竞品的结构化描述；若未命中该维度，回退到检索该类目最相关能力点。"""
        comp = self._by_name.get(competitor)
        if comp is None:
            return ""
        if dimension in comp.spec and comp.spec[dimension]:
            return comp.spec[dimension]
        # 回退：检索该竞品能力里与维度相关的一条（用维度词打分）
        hits = self.recall_by_query(dimension, top_k=1)
        relevant = [h for h in hits if h.competitor == competitor]
        if relevant:
            return relevant[0].capability
        return comp.capabilities[0] if comp.capabilities else comp.description


# 便于外部引用（与真实 solution-eval 汇报对齐）
StructuredGenerator = MockStructuredGenerator