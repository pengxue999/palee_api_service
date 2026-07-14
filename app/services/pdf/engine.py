import multiprocessing
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

from app.services.pdf.assets import BROWSER_DIR, PROJECT_ROOT


os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(BROWSER_DIR))


def _find_browser_binary() -> str | None:
    patterns = (
        "chromium-*/chrome-win/chrome.exe",
        "chromium-*/chrome-linux/chrome",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        "chromium_headless_shell-*/chrome-win/headless_shell.exe",
        "chromium_headless_shell-*/chrome-linux/headless_shell",
        "chromium_headless_shell-*/chrome-mac/headless_shell",
    )

    configured_path = PROJECT_ROOT / ".playwright-browsers"
    for browser_root in (configured_path, BROWSER_DIR):
        if not browser_root.exists():
            continue

        for pattern in patterns:
            matches = sorted(browser_root.glob(pattern), reverse=True)
            if matches:
                return str(matches[0])

    return None


def resolve_chromium_executable() -> str | None:
    chromium_executable = _find_browser_binary()
    if chromium_executable is not None:
        return chromium_executable

    BROWSER_DIR.mkdir(parents=True, exist_ok=True)
    install_env = os.environ.copy()
    install_env["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSER_DIR)
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
        env=install_env,
    )

    return _find_browser_binary()


def _render_in_subprocess(
    html: str,
    viewport_width: int,
    viewport_height: int,
    margin_top: str,
    margin_right: str,
    margin_bottom: str,
    margin_left: str,
    header_template: str | None,
    footer_template: str | None,
) -> bytes:
    """Run sync Playwright in a fresh process.

    The synchronous Playwright API spawns the browser as a child process.
    When that happens inside uvicorn's threadpool worker (which runs under an
    active uvloop event loop), the subprocess launch fails on Linux with
    ``BlockingIOError: [Errno 11] Resource temporarily unavailable``. Running
    the render in a separate process gives Playwright a clean, loop-free
    context so the browser can start normally.
    """
    from playwright.sync_api import sync_playwright

    chromium_executable = resolve_chromium_executable()

    with sync_playwright() as playwright:
        launch_kwargs = {
            "headless": True,
            "args": ["--font-render-hinting=medium"],
        }
        if chromium_executable is not None:
            launch_kwargs["executable_path"] = chromium_executable

        browser = playwright.chromium.launch(**launch_kwargs)
        try:
            page = browser.new_page(
                viewport={"width": viewport_width, "height": viewport_height},
                locale="lo-LA",
            )
            page.set_content(html, wait_until="load")
            page.emulate_media(media="screen")
            pdf_options = {
                "format": "A4",
                "landscape": viewport_width > viewport_height,
                "print_background": True,
                "margin": {
                    "top": margin_top,
                    "right": margin_right,
                    "bottom": margin_bottom,
                    "left": margin_left,
                },
                "prefer_css_page_size": True,
            }

            if header_template is not None or footer_template is not None:
                pdf_options["display_header_footer"] = True
                pdf_options["header_template"] = header_template or "<div></div>"
                pdf_options["footer_template"] = footer_template or "<div></div>"

            return page.pdf(**pdf_options)
        finally:
            browser.close()


def render_pdf_document(
    html: str,
    *,
    viewport_width: int,
    viewport_height: int,
    margin_top: str = "0mm",
    margin_right: str = "0mm",
    margin_bottom: str = "0mm",
    margin_left: str = "0mm",
    header_template: str | None = None,
    footer_template: str | None = None,
) -> bytes:
    # A single-worker pool per call keeps the browser render fully isolated
    # from the server's event loop and tears the process down afterwards.
    # "spawn" guarantees the child does not inherit uvicorn's uvloop state.
    spawn_context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=spawn_context) as executor:
        future = executor.submit(
            _render_in_subprocess,
            html,
            viewport_width,
            viewport_height,
            margin_top,
            margin_right,
            margin_bottom,
            margin_left,
            header_template,
            footer_template,
        )
        return future.result()
