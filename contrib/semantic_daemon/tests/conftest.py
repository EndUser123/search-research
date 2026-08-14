"""pytest configuration for semantic daemon tests.

Sets up the import path so that 'search_research' can be imported correctly.
"""

import sys
from pathlib import Path

# Add the search-research package root to sys.path
# pytest rootdir is P:\\\\\\packages/search-research, but we need to add it to sys.path
package_root = Path(__file__).parent.parent.parent.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))
