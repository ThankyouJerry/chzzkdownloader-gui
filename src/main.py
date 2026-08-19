"""
ClipCatcher - Main Entry Point
"""
import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from ui.main_window import MainWindow
from ui.styles import get_stylesheet
from core.config import Config


APP_VERSION = "2.0.10"


def run_smoke_check() -> int:
    """Run a lightweight packaged-app smoke check without opening the GUI."""
    from core.dependency_check import get_missing_dependencies

    missing = get_missing_dependencies()
    if missing:
        names = ", ".join(item.name for item in missing)
        print(f"SMOKE_FAIL missing dependencies: {names}")
        return 1

    print("SMOKE_OK")
    return 0


def main():
    """Main application entry point"""
    if "--smoke" in sys.argv:
        return run_smoke_check()

    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("ClipCatcher")
    app.setOrganizationName("ClipCatcher")
    app.setApplicationVersion(APP_VERSION)
    
    # Apply stylesheet
    app.setStyleSheet(get_stylesheet())
    
    # Create event loop for async support
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Load configuration
    config = Config()
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    # Run application
    with loop:
        loop.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
