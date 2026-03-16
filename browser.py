import os
import subprocess
import time
import urllib.request
from browser_use import BrowserProfile

BROWSERS = {
    "brave": {
        "exe": [
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
        "user_data": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
    },
    "chrome": {
        "exe": [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "user_data": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
    },
    "edge": {
        "exe": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "user_data": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
    },
}

CDP_PORT = 9222


def _find_exe(paths: list[str]) -> str | None:
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def _cdp_ready() -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json", timeout=1)
        return True
    except Exception:
        return False


def get_browser_profile() -> BrowserProfile:
    """
    Launch the user's real browser with their profile and a CDP debug port,
    then return a BrowserProfile that connects to it via CDP.
    This lets Browser Use control the real browser (with logins, history, etc.)
    """
    browser_name = os.getenv("BROWSER", "brave").lower().strip()
    info = BROWSERS.get(browser_name) or BROWSERS["brave"]

    exe = _find_exe(info["exe"])

    if not exe:
        # Fall back to bundled Chromium — no real profile but still works
        print("  No browser found — Browser Use will launch bundled Chromium.", flush=True)
        return BrowserProfile(headless=False)

    # Kill any existing instance so we can open the CDP debug port cleanly
    exe_name = os.path.basename(exe)
    print(f"  Closing existing {exe_name} instances...", flush=True)
    subprocess.call(["taskkill", "/F", "/IM", exe_name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)

    # Launch with CDP debug port + real user profile
    print(f"  Launching {browser_name} with user profile...", flush=True)
    subprocess.Popen([
        exe,
        f"--remote-debugging-port={CDP_PORT}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
    ])

    # Wait for CDP to become available
    for _ in range(30):
        if _cdp_ready():
            break
        time.sleep(0.5)
    else:
        raise RuntimeError(f"Browser did not open CDP port on localhost:{CDP_PORT}")

    print(f"  Browser ready on CDP port {CDP_PORT}.", flush=True)

    # Tell Browser Use to connect to the existing browser via CDP
    return BrowserProfile(
        cdp_url=f"http://localhost:{CDP_PORT}",
        headless=False,
        wait_between_actions=0.3,
        minimum_wait_page_load_time=0.5,
    )
