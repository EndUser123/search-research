"""Auto-scaffolded test for decision_schema."""

import pytest
import sys
from pathlib import Path

# Add examples directory to path for import
examples_dir = Path(__file__).parent.parent / "skills" / "decision-tree" / "references" / "examples"
sys.path.insert(0, str(examples_dir))

from decision_schema import DecisionTreeNode, create_decision_tree, example_failure_regeneration


def test_decision_tree_node_exists():
    """Smoke test: DecisionTreeNode class can be imported."""
    assert DecisionTreeNode is not None


def test_create_decision_tree():
    """Test creating a decision tree."""
    tree = create_decision_tree()
    assert tree.node_id == "root"
    assert tree.type == "selector"
    assert len(tree.children) == 3


def test_leaf_node_validation():
    """Test that leaf nodes (action, condition) cannot have children."""
    with pytest.raises(ValueError, match="cannot have children"):
        DecisionTreeNode(
            node_id="invalid",
            type="action",
            children=[DecisionTreeNode(node_id="child", type="condition")],
        )


def test_status_states():
    """Test all valid status values."""
    for status in ["pending", "running", "success", "failure"]:
        node = DecisionTreeNode(node_id="test", type="condition", status=status)
        assert node.status == status


# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_decision_schema.py -v
