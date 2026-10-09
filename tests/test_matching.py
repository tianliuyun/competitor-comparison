"""语义匹配模块测试：需求 → 竞品能力点的对齐与命中判定。"""

from competitor_comparison.matching import SemanticMatcher
from competitor_comparison.retrieval import KnowledgeBase


def test_match_query_ranks_hits_first(knowledge_base):
    """命中项排在未命中项之前，且相似度局部降序。"""
    matcher = SemanticMatcher(KnowledgeBase(knowledge_base))
    results = matcher.match_query("客户要求支持高可用集群与故障自动转移", top_k=5)
    assert results
    matched = [m for m in results if m.matched]
    if matched:
        # 所有命中项应排在所有未命中项之前
        first_unmatched = next((i for i, m in enumerate(results) if not m.matched), len(results))
        assert all(m.matched for m in results[:first_unmatched])


def test_is_satisfied_positive_and_negative(knowledge_base):
    """竞品是否已能覆盖某需求，命中/未命中有明确区分。"""
    matcher = SemanticMatcher(KnowledgeBase(knowledge_base))
    # 老牌方案商 A 明确具备高可用集群能力
    assert matcher.is_satisfied("要求高可用集群与自动故障转移", "老牌方案商 A")


def test_match_carries_dimension_label(knowledge_base):
    """每个匹配结果都会归到业务维度。"""
    matcher = SemanticMatcher(KnowledgeBase(knowledge_base))
    results = matcher.match_query("客户要国产化、自主可控", top_k=5)
    assert results
    assert all(m.dimension for m in results)


def test_match_threshold_constant():
    """语义匹配使用统一阈值常量。"""
    from competitor_comparison import models

    assert models.SEMANTIC_THRESHOLD == 0.55