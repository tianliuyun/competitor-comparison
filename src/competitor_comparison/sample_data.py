"""示例领域数据：一个「企业 IT 采购方案对比」的通用知识库。

注意：这里用完全通用的业务表述建模（桌面虚拟化/数据备份等典型企业 IT 采购场景），
不绑定任何真实厂商产品，作为开源的通用学习示例，任何人都可替换为自己的领域数据。
"""

from __future__ import annotations

from typing import Dict, List

from .models import Competitor, POSITION_STRONG, POSITION_PARITY, POSITION_GAP

# 我方产品（通用企业 IT 解决方案，各维度的描述）
OUR_SPEC: Dict[str, str] = {
    "产品定位": "面向中大型企业的一体化 IT 基础平台，强调本地化部署与国产化自主可控。",
    "核心功能": "统一接入网关、集中管控、高可用集群、细粒度权限与审计。",
    "性能指标": "支持万级并发连接，节点横向扩容，故障自动转移，低延迟体验。",
    "价格体系": "按并发数授权，TCO 友好，一次采购长期维保。",
    "生态兼容": "开放 API 与 SDK，支持与主流认证、监控、容器平台对接。",
    "服务支持": "原厂驻场与远程支持结合，SLA 5x8 起，可升级到 7x24。",
}


# 竞品 A：主打"高可用/集群/性能"的老牌方案供应商
_COMP_A = Competitor(
    name="老牌方案商 A",
    category="企业 IT 基础架构",
    description="长期服务企业级市场的成熟方案，性能规格扎实、生态集成广，价格偏高。",
    capabilities=[
        "支持集群部署与故障自动转移，可用性 99.99%",
        "万级并发连接与低延迟性能，支持横向扩容",
        "广泛的第三方集成与开放生态",
        "丰富的历史案例与行业模板",
        "全国服务体系与驻场支持",
    ],
    spec={
        "产品定位": "成熟稳健的企业 IT 基础架构，稳字当头，价格偏高。",
        "核心功能": "自研内核高可用集群、故障转移、统一管理。",
        "性能指标": "十万级并发连接，性能扎实，但扩容需按模块付费。",
        "价格体系": "中高端定价，增值模块按需计费，TCO 偏高。",
        "生态兼容": "开放的 API/SDK，主流平台集成度较高。",
        "服务支持": "厂商多级服务体系，驻场与远程支持齐全。",
    },
    # 我方相对 A 的强弱：价格/服务有优势，性能/生态是短板，其余均势
    positioning={
        "产品定位": POSITION_PARITY,
        "核心功能": POSITION_PARITY,
        "性能指标": POSITION_GAP,
        "价格体系": POSITION_STRONG,
        "生态兼容": POSITION_GAP,
        "服务支持": POSITION_STRONG,
    },
)

# 竞品 B：主打"性价比/轻量/快速交付"的新兴方案
_COMP_B = Competitor(
    name="新兴厂商 B",
    category="云原生轻量 IT 平台",
    description="主打轻量、低价、快速上手的云原生平台，性能中等，服务深度相对有限。",
    capabilities=[
        "低成本快速交付，轻量化部署",
        "云原生化，容器化支持",
        "低于行业的价格与灵活的订阅策略",
        "性能中等，不适合重负载场景",
        "远程支持为主，驻场资源有限",
    ],
    spec={
        "产品定位": "轻量、高性价比的云原生平台，主打省钱好上手。",
        "核心功能": "容器化部署，托管式运维，快速交付。",
        "性能指标": "中等水平，重负载与复杂场景支撑不足。",
        "价格体系": "定价低于主流，订阅灵活，性价比高。",
        "生态兼容": "以标准 API 对接为主，深度集成能力有限。",
        "服务支持": "远程支持为主，驻场与定制化服务资源有限。",
    },
    # 我方相对 B 的强弱：性能/生态有优势，价格是短板，其余均势
    positioning={
        "产品定位": POSITION_PARITY,
        "核心功能": POSITION_STRONG,
        "性能指标": POSITION_STRONG,
        "价格体系": POSITION_GAP,
        "生态兼容": POSITION_STRONG,
        "服务支持": POSITION_PARITY,
    },
)

# 竞品 C：主打"纵深防御/纯国产/极简"的方案（与我方差异化最大）
_COMP_C = Competitor(
    name="纯国产化厂商 C",
    category="国产自主可控方案",
    description="纯国产化栈解决方案，自主可控是其最大卖点，但生态开放度与高端性能一般。",
    capabilities=[
        "全栈国产化适配与自主可控",
        "满足监管合规的本地化部署",
        "基础性能可用，高峰值能力一般",
        "生态相对封闭，第三方对接有限",
        "区域化本地服务团队",
    ],
    spec={
        "产品定位": "纯国产自主可控，契合监管合规诉求。",
        "核心功能": "全栈国产化适配、简化部署、合规审计。",
        "性能指标": "基础性能可用，高峰值重载能力一般。",
        "价格体系": "定价适中，国产化溢价偏整理。",
        "生态兼容": "生态相对封闭，开放 API 有限。",
        "服务支持": "本地化服务为主，覆盖范围区域限定。",
    },
    # 我方相对 C 的强弱：核心功能/生态有优势，性能/服务是短板，其余均势
    positioning={
        "产品定位": POSITION_PARITY,
        "核心功能": POSITION_STRONG,
        "性能指标": POSITION_GAP,
        "价格体系": POSITION_PARITY,
        "生态兼容": POSITION_STRONG,
        "服务支持": POSITION_GAP,
    },
)

SAMPLE_COMPETITORS: List[Competitor] = [_COMP_A, _COMP_B, _COMP_C]


def build_sample_knowledge_base() -> List[Competitor]:
    """返回一份可直接用于演示/测试的竞品知识库。"""
    return [Competitor(name=c.name, category=c.category, description=c.description,
                       capabilities=list(c.capabilities), spec=dict(c.spec),
                       positioning=dict(c.positioning))
            for c in SAMPLE_COMPETITORS]


def typical_requirements() -> List[str]:
    """几段典型的客户采购需求（演示/测试用）。"""
    return [
        "客户要求方案支持高可用集群与自动故障转移，保障业务连续不中断。",
        "预算有限，希望整体采购成本可控，性价比要高。",
        "受合规监管，要求方案必须国产化、自主可控、本地化部署。",
        "需要开放 API 和生态对接，方便与现有系统集成。",
    ]