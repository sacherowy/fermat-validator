import sys
from pathlib import Path

# Make the 'app' package importable from anywhere in the test suite
sys.path.insert(0, str(Path(__file__).parent.parent))
