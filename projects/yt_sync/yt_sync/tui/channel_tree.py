"""
Channel tree display components for the TUI.
"""

from typing import Any

from textual.widgets import Tree


class EnhancedChannelTree(Tree):
    def clear_tree(self):
        """Clear all channel nodes and reinitialize the tree sections."""
        # Remove all children from the root node
        while self.root.children:
            self.root.children[-1].remove()
        self.channel_nodes.clear()
        self.processing_node = self.root.add("🔄 Processing", expand=True)
        self.completed_node = self.root.add("✅ Completed", expand=True)
        self.failed_node = self.root.add("❌ Failed", expand=False)

    """Enhanced channel tree with better organization."""

    def __init__(self):
        super().__init__("📺 Channel Pipeline", id="enhanced-channel-tree")
        self.root.expand()
        self.channel_nodes: dict[str, Any] = {}

        self.processing_node = self.root.add("🔄 Processing", expand=True)
        self.completed_node = self.root.add("✅ Completed", expand=True)
        self.failed_node = self.root.add("❌ Failed", expand=False)

    def add_channel_node(self, channel_name: str, status: str = "processing"):
        """Add a new channel to the appropriate section."""
        if status == "processing":
            node = self.processing_node.add(f"🔄 {channel_name}")
        elif status == "failed":
            node = self.failed_node.add(f"❌ {channel_name}")
        else:
            node = self.completed_node.add(f"✅ {channel_name}")

        self.channel_nodes[channel_name] = node
        return node

    def update_channel_status(
        self, channel_name: str, status: str, stats: dict[str, Any] | None = None
    ):
        """Update channel status and move to appropriate section."""
        if channel_name in self.channel_nodes:
            old_node = self.channel_nodes[channel_name]
            old_node.remove()

        if status == "failed":
            node = self.failed_node.add(f"❌ {channel_name}")
        else:
            stats_text = ""
            if stats:
                new_vids = stats.get("new_videos", 0)
                upgrades = stats.get("upgrades", 0)
                if new_vids > 0 or upgrades > 0:
                    stats_text = f" (New: {new_vids}, Up: {upgrades})"

            node = self.completed_node.add(f"✅ {channel_name}{stats_text}")

        self.channel_nodes[channel_name] = node
