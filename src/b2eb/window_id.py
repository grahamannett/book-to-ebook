#!/usr/bin/env python3
import sys

import Quartz.CoreGraphics as CG
from AppKit import NSRunningApplication, NSWorkspace
from ApplicationServices import AXUIElementCreateApplication
from Foundation import NSArray, NSDictionary, NSString
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowBounds,
    kCGWindowListExcludeDesktopElements,
    kCGWindowName,
    kCGWindowNumber,
    kCGWindowOwnerName,
)


def print_usage(program_name):
    print(f"""Usage: {program_name} <application-bundle-name> <window-title>

For example, to get the ID of the iOS/tvOS/watchOS Simulator:
    {program_name} Simulator 'iPhone X - iOS 11.0'

…and to capture a screenshot of it:
    screencapture -l$({program_name} Simulator 'iPhone X - iOS 11.0') simulator.png

To get the ID of a window without a title, pass an empty string as the title:
    {program_name} GLFW ''

To list all of an app's windows, pass `--list` as the title:
    {program_name} Simulator --list""")


def get_window_title_from_accessibility(window, bounds):
    # Try to get window title using Accessibility API if not available through CGWindow
    try:
        ax_app = AXUIElementCreateApplication(window[kCGWindowOwnerPID])
        windows = None

        # Get windows attribute
        windows_ref = Quartz.AXUIElementCopyAttributeValue(ax_app, Quartz.kAXWindowsAttribute)
        if windows_ref:
            windows = windows_ref.get()

        if windows:
            for ax_window in windows:
                # Check if window matches based on position and size
                possible_match = True

                # Check position
                position = Quartz.AXUIElementCopyAttributeValue(ax_window, Quartz.kAXPositionAttribute)
                if position:
                    p = position.get()
                    if p.x != bounds.origin.x or p.y != bounds.origin.y:
                        possible_match = False

                # Check size
                size = Quartz.AXUIElementCopyAttributeValue(ax_window, Quartz.kAXSizeAttribute)
                if size:
                    s = size.get()
                    if s.width != bounds.size.width or s.height != bounds.size.height:
                        possible_match = False

                if possible_match:
                    title = Quartz.AXUIElementCopyAttributeValue(ax_window, Quartz.kAXTitleAttribute)
                    if title:
                        return title.get()
    except Exception as e:
        pass
    return None


def main():
    if len(sys.argv) != 3:
        print_usage(sys.argv[0])
        return -1

    # Check if running in GUI session
    session = CG.CGSessionCopyCurrentDictionary()
    if not session:
        print(f"""Warning: {sys.argv[0]} is not running within a Quartz GUI session,
so it won't be able to retrieve information on any windows.

If you're using continuous integration, consider launching
your agent as a GUI process (an `.app` bundle started via
System Preferences > Users & Group > Login Items)
instead of using a LaunchDaemon or LaunchAgent.""")

    requested_app = sys.argv[1]
    requested_window = sys.argv[2]
    show_list = requested_window == "--list"
    app_found = False

    # Get window list
    windows = CGWindowListCopyWindowInfo(kCGWindowListExcludeDesktopElements, kCGNullWindowID)

    for window in windows:
        current_app = window.get(kCGWindowOwnerName, "")
        current_window_title = window.get(kCGWindowName, "")
        bounds = CG.CGRectMakeWithDictionaryRepresentation(window[kCGWindowBounds], None)[1]

        if bounds.size.height == 0 or bounds.size.width == 0:
            print(f"Skipping window with zero size: {window=}")
            continue

        if current_app == requested_app:
            app_found = True

            # Check aspect ratio to filter out menu bar
            aspect = bounds.size.width / bounds.size.height
            if aspect > 30:
                continue

            # Try to get window title from accessibility API if not available
            if not current_window_title:
                current_window_title = get_window_title_from_accessibility(window, bounds)

            # Skip focus proxy windows
            if current_window_title == "Focus Proxy" and bounds.size.width == 1 and bounds.size.height == 1:
                continue

            if show_list:
                print(
                    f'"{current_window_title}" size={bounds.size.width}x{bounds.size.height} '
                    f"id={window[kCGWindowNumber]}"
                )
                continue

            if current_window_title == requested_window or (not current_window_title and not requested_window):
                print(window[kCGWindowNumber])
                return 0

    return 0 if show_list and app_found else -2


if __name__ == "__main__":
    sys.exit(main())
