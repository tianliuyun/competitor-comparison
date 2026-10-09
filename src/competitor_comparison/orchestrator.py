"""编排模块：把检索 / 匹配 / 结构化生成串成一条完整流水线。

这是对外业务 API：
- 构建一次对比 = 输入（我方产品维度描述 + 竞品知识库）
- 产出 = 面向一个竞品的结构化对比报告（含逐维度对比 + 赢单策略总评）

面向销售的入口 `CompetitorComparisonAssistant` 只暴露一个业务动作：
`compare(requirement, top_competitors)` —— 销售描述客户需求，系统自动回整份对比报告。
"""

from __future__ import annotations

from typing import List

from .generation import StructuredReportGenerator
from .matching import SemanticMatcher
from .models import Competitor, ComparisionReport, DEFAULT_DIMENSIONS
from .retrieval import KnowledgeBase


class ComparisonPipeline:
    """完整流水线：KB(检索) → Matcher(匹配) → Generator(生成) → 报告。"""

    def __init__(
        self,
        kb: KnowledgeBase,
        matcher: SemanticMatcher,
        generator: StructuredReportGenerator,
        our_spec: dict,
    ) -> None:
        self.kb = kb
        self.matcher = matcher
        self.generator = generator
        self.our_spec = dict(our_spec)

    def run(self, competitor_name: str) -> ComparisionReport:
        """对指定竞品生成完整对比报告。"""
        return self.generator.build_report(self.our_spec, competitor_name)

    def rank_competitors(self, requirement: str, top_k: int = 3) -> List[str]:
        """基于语义匹配，按需求相关性给竞品排序（优先级最高的排前面）。"""
        matched = self.matcher.match_query(requirement, top_k=20)
        # 按出现频次 + 命中优先聚合竞品
        score: dict = {}
        for m in matched:
            score[m.competitor] = score.get(m.competitor, 0.0) + (m.similarity if m.matched else 0.1)
        ranked = sorted(score.keys(), key=lambda c: -score[c])
        return ranked[:top_k]

    def compare(self, requirement: str, top_competitors: int = 3) -> List[ComparisionReport]:
        """一键入口：给定客户需求，自动对"最相关的若干竞品"各生成一份对比报告。"""
        names = self.rank_competitors(requirement, top_k=top_competitors)
        return [self.generator.build_report(self.our_spec, name) for name in names]


class CompetitorComparisonAssistant:
    """面向业务的一句话入口（给销售/售前用的门面）。"""

    def __init__(self, our_spec: dict, knowledge_base: List[Competitor]) -> None:
        self._pipeline = _make_pipeline(our_spec, knowledge_base)

    def compare(self, requirement: str, top_competitors: int = 3) -> List[ComparisionReport]:
        reports = self._pipeline.compare(requirement, top_competitors=top_competitors)
        return reports

    @property
    def pipeline(self) -> ComparisonPipeline:
        return self._pipeline


def _make_pipeline(our_spec: dict, knowledge_base: List[Competitor]) -> ComparisonPipeline:
    kb = KnowledgeBase(knowledge_base)
    matcher = SemanticMatcher(kb)
    generator = StructuredReportGenerator(kb)
    return ComparisonPipeline(kb, matcher, generator, our_spec)