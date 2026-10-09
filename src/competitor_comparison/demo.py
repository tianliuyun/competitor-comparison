"""本地演示脚本：一次跑通"客户需求 → 竞品对比报告"。

用法：
    python -m competitor_comparison.demo

完全离线运行，无需 API Key。
"""

from __future__ import annotations

from .orchestrator import CompetitorComparisonAssistant
from .sample_data import OUR_SPEC, SAMPLE_COMPETITORS, typical_requirements


def _print_report(report, index: int) -> None:
    print(f"\n================= 对比报告 {index}：{report.competitor_name} =================")
    print(f"对比维度数：{report.dimensions_compared}")
    for row in report.rows:
        print(f"\n[维度 {row.dimension}]  结论：{row.conclusion}")
        print(f"  我方：{row.ours}")
        print(f"  竞品：{row.theirs}")
        print(f"  依据：{row.evidence}")
    print(f"\n>>> 赢单策略总评：{report.summary}")


def main() -> None:
    print("「竞品方案对比分析助手」本地演示（Mock 后端，离线运行）")
    print("=" * 60)
    print("已加载竞品知识库：")
    for c in SAMPLE_COMPETITORS:
        print(f"  - {c.name}（{c.category}，能力点 {len(c.capabilities)} 条）")

    assistant = CompetitorComparisonAssistant(OUR_SPEC, SAMPLE_COMPETITORS)

    print("\n示例客户需求：")
    for i, req in enumerate(typical_requirements()):
        print(f"  {i + 1}. {req}")

    # 跑第一段需求，对最相关的 2 个竞品生成对比报告
    requirement = typical_requirements()[0]
    print(f"\n>>> 正在处理需求：{requirement}")
    reports = assistant.compare(requirement, top_competitors=2)
    for i, r in enumerate(reports, start=1):
        _print_report(r, i)

    print("\n演示完成。")


if __name__ == "__main__":
    main()