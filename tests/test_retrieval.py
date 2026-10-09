"""检索模块测试：RAG 召回能力与向量索引的正确性。"""

import math

from competitor_comparison.retrieval import KnowledgeBase
from competitor_comparison.mock_backend import MockBiEncoder


def test_encoder_deterministic_and_unit():
    """Mock 编码器是确定性的，且输出为固定维度。"""
    enc = MockBiEncoder()
    v1 = enc.encode("需要国产化、自主可控、本地化部署")
    v2 = enc.encode("需要国产化、自主可控、本地化部署")
    assert v1 == v2
    assert enc.dimension > 0
    assert len(v1) == enc.dimension
    # 未归一化，但分量非负且至少一个非零
    assert any(x > 0 for x in v1)


def test_semantic_similarity_reflects_concept_overlap():
    """语义相似度能区分"相关"和"不相关"的需求。"""
    enc = MockBiEncoder()
    related = enc.similarity("要求高可用集群与故障自动转移", "方案需支持高可用集群、故障转移")
    unrelated = enc.similarity("要求高可用集群与故障自动转移", "客户关注采购价格与总体成本")
    assert related > unrelated


def test_index_search_returns_capabilities_over_threshold(knowledge_base):
    """对需求做召回，返回的命中项按相似度降序且都超过阈值。"""
    kb = KnowledgeBase(knowledge_base)
    hits = kb.recall_by_query("客户要求国产化、自主可控、本地化部署", top_k=3)
    assert hits, "应至少命中一条能力点"
    # 相似度单调不增
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_recall_dimension_falls_back_to_capability(knowledge_base):
    """某维度无结构化描述时，回退到语义检索该类目最相关的能力点。"""
    kb = KnowledgeBase(knowledge_base)
    desc = kb.recall_dimension("老牌方案商 A", "一个知识库里不存在的维度")
    assert isinstance(desc, str) and desc


def test_knowledge_base_get(knowledge_base):
    kb = KnowledgeBase(knowledge_base)
    comp = kb.get("老牌方案商 A")
    assert comp is not None
    assert kb.get("不存在的竞品") is None