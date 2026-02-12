"""
Pytest Configuration - Test Setup & Fixtures
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "app" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent.parent))

# Add app/backend to path for imports
os.chdir(backend_path.parent.parent)

# Import all models to ensure Base is properly initialized
try:
    from models.base import Base
    from models.restaurant import Restaurant, RestaurantStatus
    from models.canonical_menu import CanonicalMenu
    from models.menu_upload import MenuUploadTask
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
