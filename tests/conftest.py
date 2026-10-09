"""pytest 共享夹具：统一的演示知识库 + 我方产品描述。"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from competitor_comparison.sample_data import (  # noqa: E402
    OUR_SPEC,
    SAMPLE_COMPETITORS,
    build_sample_knowledge_base,
)


@pytest.fixture(scope="session")
def knowledge_base():
    """可复用的竞品知识库（3 个竞品）。"""
    return build_sample_knowledge_base()


@pytest.fixture(scope="session")
def our_spec():
    """我方产品各维度描述（与 demo 一致）。"""
    return dict(OUR_SPEC)


@pytest.fixture(scope="session")
def sample_competitors():
    return SAMPLE_COMPETITORS