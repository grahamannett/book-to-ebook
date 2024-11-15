#!/usr/bin/env python3

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .constants import output_dir


@dataclass
class KindleConfig:
    """Configuration settings for Kindle screenshot automation."""

    app_name: str = "Kindle"
    bundle_name: str = "Kindle"  # Bundle name for GetWindowID
    startup_delay: int = 3
    page_turn_delay: float = 0.5
    screenshot_delay: float = 0.5
    output_dir: str = f"{output_dir}/kindle_screenshots"


class WindowManager:
    """Manages window operations for the Kindle application."""

    def __init__(self, config: KindleConfig):
        self.config = config
        self._window_id: Optional[str] = None

    def focus_window(self) -> None:
        """Focus the Kindle application window using AppleScript."""
        apple_script = f"""
        tell application "{self.config.app_name}"
            activate
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script], check=True)
        time.sleep(1)  # Allow window to focus

    @property
    def window_id(self) -> str:
        """Get or cache the window ID using GetWindowID command."""
        if self._window_id is None:
            if not shutil.which("GetWindowID"):
                raise EnvironmentError(
                    "GetWindowID not found. Install with: " "brew install smokris/getwindowid/getwindowid"
                )

            result = subprocess.run(
                ["GetWindowID", self.config.bundle_name, self.config.bundle_name],
                capture_output=True,
                text=True,
                check=True,
            )
            self._window_id = result.stdout.strip()

            if not self._window_id:
                raise RuntimeError("Failed to get window ID")

        return self._window_id


class ScreenshotManager:
    """Manages screenshot operations."""

    def __init__(self, config: KindleConfig, window_manager: WindowManager):
        self.config = config
        self.window_manager = window_manager
        self.output_path = Path(config.output_dir)
        self._setup_output_directory()

    def _setup_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_path.mkdir(parents=True, exist_ok=True)

    def take_screenshot(self, page_num: int) -> Path:
        """Take a screenshot of the current window and save it."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_path / f"page_{page_num:03d}_{timestamp}.png"

        subprocess.run(["screencapture", "-l", self.window_manager.window_id, "-x", str(filename)], check=True)

        return filename


class KindleAutomation:
    """Main automation class for Kindle screenshot process."""

    def __init__(self, num_pages: int, config: Optional[KindleConfig] = None):
        self.config = config or KindleConfig()
        self.num_pages = num_pages
        self.window_manager = WindowManager(self.config)
        self.screenshot_manager = ScreenshotManager(self.config, self.window_manager)
        self.logger = self._setup_logging()

    @staticmethod
    def _setup_logging() -> logging.Logger:
        """Configure logging for the automation."""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        return logging.getLogger(__name__)

    def _setup_pyautogui(self) -> None:
        """Configure PyAutoGUI settings."""
        try:
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5
        except ImportError:
            self.logger.error("PyAutoGUI not installed. Installing required packages...")
            subprocess.run(["pip3", "install", "pyautogui"], check=True)
            self.logger.info("Please run the script again.")
            raise SystemExit(1)

    def run(self) -> None:
        """Execute the main automation process."""
        self._setup_pyautogui()
        import pyautogui  # Import here after ensuring it's installed

        self.logger.info(f"Starting automation in {self.config.startup_delay} seconds...")
        time.sleep(self.config.startup_delay)

        self.window_manager.focus_window()

        for page_num in range(1, self.num_pages + 1):
            try:
                filename = self.screenshot_manager.take_screenshot(page_num)
                self.logger.info(f"Captured page {page_num} to {filename}")

                pyautogui.press("right")
                time.sleep(self.config.page_turn_delay)

            except Exception as e:
                self.logger.error(f"Error on page {page_num}: {str(e)}")
                break

            time.sleep(self.config.screenshot_delay)


def main():
    """Main entry point for the script."""
    num_pages = 378  # Can be modified or made into a command line argument

    try:
        automation = KindleAutomation(num_pages)
        automation.run()
    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
