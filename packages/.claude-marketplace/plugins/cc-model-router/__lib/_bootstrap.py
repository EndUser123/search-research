"""Bootstrap for cc-model-router plugin."""

import os
import sys

def bootstrap():
    """Set up paths for cc-model-router hooks."""
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hooks_dir = os.path.join(plugin_root, 'hooks')
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)
    return plugin_root

if __name__ == '__main__':
    bootstrap()
