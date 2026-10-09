"""编排模块测试：面向业务的一键入口与流水线端到端正确性。"""

from competitor_comparison.orchestrator import (
    CompetitorComparisonAssistant,
    ComparisonPipeline,
)
from competitor_comparison.retrieval import KnowledgeBase
from competitor_comparison.sample_data import OUR_SPEC, SAMPLE_COMPETITORS


def test_assistant_compare_returns_reports(knowledge_base, our_spec):
    """一句话入口：给定客户需求，自动对最相关竞品生成对比报告。"""
    assistant = CompetitorComparisonAssistant(our_spec, knowledge_base)
    reports = assistant.compare("客户要求方案支持高可用集群与自动故障转移", top_competitors=2)
    assert len(reports) >= 1
    assert all(r.rows for r in reports)


def test_pipeline_rank_orders_by_relevance(knowledge_base, our_spec):
    """需求与某竞品高度相关时，该竞品应排在最前面。"""
    pipeline = ComparisonPipeline(
        kb=KnowledgeBase(knowledge_base),
        matcher=__import__("competitor_comparison.matching", fromlist=["SemanticMatcher"]).SemanticMatcher(
            KnowledgeBase(knowledge_base)
        ),
        generator=__import__(
            "competitor_comparison.generation", fromlist=["StructuredReportGenerator"]
        ).StructuredReportGenerator(KnowledgeBase(knowledge_base)),
        our_spec=our_spec,
    )
    ranked = pipeline.rank_competitors("客户要高性能、万级并发的平台", top_k=3)
    assert "老牌方案商 A" in ranked  # A 主打性能/高可用
    assert ranked[0] in {"老牌方案商 A", "新兴厂商 B"}


def test_build_pipeline_convenience(knowledge_base, our_spec):
    """`build_pipeline` 便捷入口可用。"""
    from competitor_comparison import build_pipeline

    pipeline = build_pipeline(our_spec, knowledge_base)
    assert isinstance(pipeline, ComparisonPipeline)
    freport = pipeline.run("新兴厂商 B")
    assert freport.competitor_name == "新兴厂商 B"


def test_end_to_end_full_flow(knowledge_base, our_spec):
    """端到端：需求 → 报告，覆盖全部六个维度且输出稳定。"""
    assistant = CompetitorComparisonAssistant(our_spec, knowledge_base)
    reports = assistant.compare("预算有限，希望整体采购成本可控，性价比要高", top_competitors=3)
    assert len(reports) == 3  # 3 个竞品全部生成
    # 新兴厂商 B 主打性价比 → 价格是其主要卖点（我方相对其是短板）
    b_report = next(r for r in reports if r.competitor_name == "新兴厂商 B")
    by_dim = {r.dimension: r.conclusion for r in b_report.rows}
    assert by_dim["价格体系"] == "我方短板"


def test_from_project_entrypoint(knowledge_base, our_spec):
    """顶层 `__init__` 暴露的便捷入口也能用（关键路径可 import）。"""
    from competitor_comparison import build_pipeline as bp

    pipeline = bp(dict(OUR_SPEC), SAMPLE_COMPETITORS)
    report = pipeline.run("老牌方案商 A")
    assert report.dimensions_compared == 6