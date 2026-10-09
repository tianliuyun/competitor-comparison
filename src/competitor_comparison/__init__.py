"""竞品方案对比分析助手 —— 包入口。

对外暴露高层 API：
- `build_pipeline(our_spec, knowledge_base)` 组装完整对比流水线
- `CompetitorComparisonAssistant` 面向业务的一句话入口
"""

from .models import ComparisionReport, Competitor
from .orchestrator import ComparisonPipeline, CompetitorComparisonAssistant

__all__ = [
    "Competitor",
    "ComparisionReport",
    "ComparisonPipeline",
    "CompetitorComparisonAssistant",
    "build_pipeline",
]

__version__ = "0.1.0"


def build_pipeline(our_spec: dict, knowledge_base: list):
    """便捷入口：直接由我方产品维度和竞品知识库组装完整对比流水线。

    参数
    ----
    our_spec : dict
        我方产品在各维度的描述，键为维度名（如 "产品定位"、"性能指标"）。
    knowledge_base : list[Competitor]
        竞品列表。

    返回
    ----
    ComparisonPipeline
    """
    from .retrieval import KnowledgeBase
    from .matching import SemanticMatcher
    from .generation import StructuredReportGenerator

    kb = KnowledgeBase(knowledge_base)
    return ComparisonPipeline(
        kb=kb,
        matcher=SemanticMatcher(kb),
        generator=StructuredReportGenerator(kb),
        our_spec=our_spec,
    )