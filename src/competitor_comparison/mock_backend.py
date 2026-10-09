"""轻量 Mock 语义后端。

本项目刻意不依赖真实 LLM API / 向量数据库，让测试和演示在**离线环境秒级跑通**。
这里实现的是一个可替换的接口层 + 一个确定性的 Mock 实现：

- `EmbeddingBackend`：encode(query) -> 向量，底层可换成真实 BiEncoder（如 sentence-transformers）
- `MockBiEncoder`：基于词典命中 + 关键词重叠的确定性打分，模拟语义相似
- `MockStructuredGenerator`：基于词典+规则输出结构化 JSON，模拟 LLM 的 guided_json 输出

设计原则：所有搞怪/兜底只出现在 Mock 层，上层的检索/匹配/编排逻辑与真实实现完全一致，
因此换真后端时业务代码零改动。
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

# ---- 全局词典（语义命中的"概念词典"） ----
# 每个概念下挂了同义/相关表述，用于模拟 embedding 的语义等价
_CONCEPT_LEXICON: Dict[str, List[str]] = {
    "国产化": ["国产化", "自主可控", "信创", "本地化部署", "核心自主", "安全可控"],
    "高可用": ["高可用", "集群", "故障转移", "容错", "冗余", "双活", "主备"],
    "性能": ["性能", "吞吐", "并发", "延迟", "吞吐量", "并发连接数", "扩容"],
    "价格": ["价格", "成本", "费用", "预算", "性价比", "采购成本", "TCO", "总体拥有成本"],
    "开放生态": ["开放生态", "API", "SDK", "二次开发", "对接", "集成", "插件", "生态"],
    "服务": ["服务", "响应", "SLA", "驻场", "售后", "支持", "维保", "原厂服务"],
}


def _tokenize(text: str) -> List[str]:
    """粗粒度分词：中文字符按"概念词 + 低频词"切，英文字母数字串保留。"""
    tokens: List[str] = []
    # 英文/数字串
    for en in re.findall(r"[A-Za-z0-9]+", text):
        tokens.append(en.lower())
    # 中文：先把词典里出现过的多字概念词摘出来
    rest = text
    for concept, syns in _CONCEPT_LEXICON.items():
        for syn in syns:
            if syn in rest:
                tokens.append(concept)
                rest = rest.replace(syn, " ")
    # 再按标点切分剩余中文
    for d in re.split(r"[\s，。,．；;：:、()（）/]+", rest):
        if d:
            tokens.append(d)
    return tokens


class _Eligible:
    """词典外的词也贪心地收进向量（保留 idf 感），让 OOV 词也能贡献相似度。"""

    MIN_LEN = 2


class MockBiEncoder:
    """确定性语义编码器（Mock）。

    把文本编码成「在概念空间上的稀疏命中向量」：向量维度 = 概念词典维度，
    每个概念的出现次数作为分量。因为词典是固定的，两个文本的余弦相似度
    可复现、可断言，正好满足离线测试。

    要换成真实 BiEncoder，只需实现同名的 `encode(text) -> List[float]`。
    """

    def __init__(self) -> None:
        self._concepts = sorted(_CONCEPT_LEXICON.keys())
        self._dim = len(self._concepts)

    @property
    def dimension(self) -> int:
        return self._dim

    def encode(self, text: str) -> List[float]:
        text = str(text or "").lower()
        toks = _tokenize(text)
        vec = [0.0] * self._dim
        for tok in toks:
            # 命中的概念词直接累加权重
            for i, concept in enumerate(self._concepts):
                if tok == concept or _sync_atom_match(tok, concept):
                    vec[i] += 1.0
                    break
            else:
                # 词典外词：给"性能"一个很小的洪泛权重（模拟 embedding 的全局分布）
                vec[self._concepts.index("性能")] += 0.15
        return vec

    def similarity(self, a: str, b: str) -> float:
        """余弦相似度（带平滑，避免零向量）。"""
        va = self.encode(a)
        vb = self.encode(b)
        return _cosine(va, vb)


def _sync_atom_match(tok: str, concept: str) -> bool:
    """把用户话里最贴近概念的原词也归进该概念（近似同义词）。"""
    concept_syns = _CONCEPT_LEXICON.get(concept, [])
    if any(syn in tok for syn in concept_syns):
        return True
    # 两字重叠即视为同义，如 "国产" ~ "国产化"
    return tok and concept and len(tok) >= 2 and tok in concept or (concept in tok and len(concept) >= 2)


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = (sum(x * x for x in a) ** 0.5) or 1e-9
    nb = (sum(y * y for y in b) ** 0.5) or 1e-9
    return dot / (na * nb)


# ---- 检索需要的编码器接口别名 ----
EmbeddingBackend = MockBiEncoder


class MockStructuredGenerator:
    """Mock 的 guided_json 结构化生成器。

    真实方案中由 LLM + JSON Schema 约束解码完成；这里用确定性规则复现同一种输出契约：
    输入 `(我方维度描述, 竞品维度描述, 相似度)`，输出结构化 JSON dict。

    返回的 schema 与真实版本保持一致：
    {
      "dimension": str,
      "ours": str,
      "theirs": str,
      "conclusion": "我方优势" | "势均力敌" | "我方短板",
      "evidence": str,
    }
    """

    @staticmethod
    def compare_cell(ours: str, theirs: str, similarity: float, position: int = 0) -> Dict[str, Any]:
        """生成一个对比单元格。

        结论来自领域竞争定位模型 `position`（我方相对强弱），语义相似度作为佐证证据。
        position 取值：+1 我方优势 / 0 势均力敌 / -1 我方短板。
        """
        conclusion = _pick_conclusion_from_position(position)
        evidence = _build_evidence(ours, theirs, similarity)
        return {
            "dimension": _guess_dimension(ours, theirs),
            "ours": ours,
            "theirs": theirs,
            "conclusion": conclusion,
            "evidence": evidence,
        }

    @staticmethod
    def generate_summary(combination: List[Dict[str, Any]], strong: List[str], gap: List[str]) -> str:
        n_gap = len(gap)
        strong_part = "、".join(strong) if strong else "无明显优势"
        if n_gap == 0:
            verdict = "我方在全部维度具备可对外表述的确定性优势，建议正面进攻。"
        elif n_gap <= 1:
            verdict = f"我方整体占优，仅 {n_gap} 个维度需补强，建议针对 {gap[0]} 提前准备话术。"
        else:
            verdict = f"我方在 {n_gap} 个维度存在短板，建议走差异化价值打法，绕开正面参数对比。"
        return f"综合评估：本轮对比共 {len(combination)} 个维度，优势维度：{strong_part}；{verdict}"


def _pick_conclusion(similarity: float) -> str:
    """基于相似度推导竞争结论：相似度越高说明竞品越能对标，我方差异化空间越小。"""
    from .models import GAP, PARITY, STRENGTH

    if similarity < 0.35:
        return STRENGTH  # 竞品几乎不覆盖我方卖点 → 我方优势
    if similarity < 0.55:
        return PARITY  # 双方接近 → 势均力敌（注意 0.55 是语义命中阈值，此处含义不同）
    return GAP  # 竞品在该点高度对齐甚至更强 → 我方短板


def _pick_conclusion_from_position(position: int) -> str:
    """由领域竞争定位模型得出结论分档。"""
    from .models import GAP, PARITY, STRENGTH, POSITION_GAP, POSITION_STRONG

    if position == POSITION_STRONG:
        return STRENGTH
    if position == POSITION_GAP:
        return GAP
    return PARITY


def _build_evidence(ours: str, theirs: str, similarity: float) -> str:
    return f"需求与竞品能力语义相似度 {similarity:.2f}；我方『{ours}』 vs 竞品『{theirs}』"


def _guess_dimension(ours: str, theirs: str) -> str:
    text = f"{ours} {theirs}"
    for dim, syns in _CONCEPT_LEXICON.items():
        for syn in syns:
            if syn in text:
                return dim
    return "其他"


class GuidedJsonBackend:
    """语义后端统一接口：Mock 结构化生成器在此处被包装成 guided_json 的形态。"""

    def generate(self, prompt: str) -> Dict[str, Any]:
        # 演示接口：真实实现为 LLM 请求，这里返回一个标注 mock 的占位
        return {"mock": True, "prompt_md5": _md5(prompt)}


def _md5(s: str) -> str:
    import hashlib

    return hashlib.md5(s.encode("utf-8")).hexdigest()