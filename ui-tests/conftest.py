from pathlib import Path

import pytest
from playwright.sync_api import expect

AUTH_FILE = Path(__file__).resolve().parent.parent / "secrets" / "rhombus-auth.json"
PROJECT_URL = "https://rhombusai.com/workflow/5325"

expect.set_options(timeout=15_000)  # wait up to 15 s for the app; no fixed sleeps


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    if not AUTH_FILE.exists():
        pytest.skip("No saved login. Run: python -m playwright codegen "
                    "--save-storage=secrets/rhombus-auth.json " + PROJECT_URL)
    return {**browser_context_args,
            "storage_state": str(AUTH_FILE),
            "viewport": {"width": 3840, "height": 1200}}


@pytest.fixture
def project_page(page):
    # Rhombus sometimes shows a false "Ad Blocker Detected" dialog in a clean
    # browser. Whenever it appears, click "Continue Anyway" and carry on.
    page.add_locator_handler(
        page.get_by_role("dialog", name="Ad Blocker Detected"),
        lambda *_: page.get_by_role("button", name="Continue Anyway").click(),
    )
    page.goto(PROJECT_URL)
    expect(page.get_by_test_id("rf__node-input_node_1")).to_be_visible(timeout=30_000)
    return page
