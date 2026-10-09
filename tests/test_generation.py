"""结构化生成模块测试：对比报告结构、维度覆盖与结论正确性。"""

from competitor_comparison.generation import StructuredReportGenerator
from competitor_comparison.models import STRENGTH
from competitor_comparison.retrieval import KnowledgeBase


def test_build_report_structural_shape(knowledge_base, our_spec):
    """完整对比报告应覆盖全部维度且行结构字段齐全。"""
    gen = StructuredReportGenerator(KnowledgeBase(knowledge_base))
    report = gen.build_report(our_spec, "老牌方案商 A")
    assert report.dimensions_compared >= 5  # 示例库是 6 维度
    assert len(report.rows) == report.dimensions_compared
    for row in report.rows:
        assert row.dimension and row.ours and row.theirs and row.conclusion
        assert row.conclusion in {"我方优势", "势均力敌", "我方短板"}
    assert report.summary


def test_build_report_unknown_competitor_raises(knowledge_base, our_spec):
    """对知识库外的竞品生成报告应抛出 KeyError，避免静默出空结果。"""
    gen = StructuredReportGenerator(KnowledgeBase(knowledge_base))
    import pytest

    with pytest.raises(KeyError):
        gen.build_report(our_spec, "不存在的竞品")


def test_build_report_respects_positioining(knowledge_base, our_spec):
    """结论应遵循领域定位模型：价格维度我方相对 A 是优势、性能是短板。"""
    gen = StructuredReportGenerator(KnowledgeBase(knowledge_base))
    report = gen.build_report(our_spec, "老牌方案商 A")
    by_dim = {r.dimension: r.conclusion for r in report.rows}
    assert by_dim["价格体系"] == "我方优势"
    assert by_dim["性能指标"] == "我方短板"


def test_report_aggregates_strong_dimensions(knowledge_base, our_spec):
    """赢单策略总评应包含被我方优势的维度清单。"""
    gen = StructuredReportGenerator(KnowledgeBase(knowledge_base))
    report = gen.build_report(our_spec, "老牌方案商 A")
    assert STRENGTH in [r.conclusion for r in report.rows]
    assert report.matched_strong  # 不应为空
    assert all(r.dimension in report.matched_strong for r in report.rows if r.conclusion == STRENGTH)


def test_to_dict_serializable(knowledge_base, our_spec):
    """报告可序列化为纯 dict（用于 JSON 输出/演示）。"""
    import json

    gen = StructuredReportGenerator(KnowledgeBase(knowledge_base))
    report = gen.build_report(our_spec, "老牌方案商 A")
    json.dumps(report.to_dict())  # 不抛异常即可序列化