"""UI tests for the Rhombus AI project (read-only: no runs, no AI prompts, no credits).

Uses the saved login in secrets/rhombus-auth.json.
Run: pytest ui-tests -v      (add --headed --slowmo 300 to watch it)
"""
import re

from playwright.sync_api import Page, expect

PIPELINE_NODES = "[data-testid^='rf__node-']"


def expect_whole_pipeline_on_screen(page: Page) -> None:
    # The canvas only draws nodes that are on screen, so conftest.py uses a very
    # wide window. Both ends of the pipeline must be visible.
    expect(page.get_by_test_id("rf__node-input_node_1")).to_be_visible()
    expect(page.locator(PIPELINE_NODES).filter(has_text="Data Output")).to_be_visible()


def open_executions(page: Page) -> None:
    page.get_by_role("tab", name="Schedule").click()
    # The clock icon has no accessible name, so we use its position:
    # the 2nd icon button on the schedule card (pencil, clock, bell, ...).
    page.locator(".flex.flex-shrink-0.items-center.gap-2 > button:nth-child(2)").click()


def test_project_opens_with_full_pipeline(project_page: Page):
    page = project_page
    expect(page).to_have_url(re.compile(r"/workflow/5325"))
    expect_whole_pipeline_on_screen(page)
    nodes = page.locator(PIPELINE_NODES)
    expect(nodes).to_have_count(10)  # Data Input + 8 cleaning nodes + Data Output
    expect(nodes.filter(has_text="Data Input")).to_have_count(1)
    expect(nodes.filter(has_text="Data Output")).to_have_count(1)
    expect(nodes.filter(has_text="Custom")).to_have_count(8)


def test_s3_source_is_connected(project_page: Page):
    page = project_page
    expect_whole_pipeline_on_screen(page)
    page.get_by_test_id("rf__node-input_node_1").click()
    page.get_by_role("button", name="Third Party Sources").click()
    expect(page.get_by_text("s3-input")).to_be_visible()
    expect(page.locator(".third-party-modal-status-success").first).to_have_text("Connected")
    expect(page.get_by_text("s3://khf-rhombus-input/input/")).to_be_visible()
    page.get_by_role("button", name="Cancel").click()
    expect(page.get_by_text("s3://khf-rhombus-input/input/")).to_be_hidden()


def test_schedule_is_set_every_15_minutes(project_page: Page):
    page = project_page
    page.get_by_role("tab", name="Schedule").click()
    expect(page.get_by_text(re.compile(r"\*/15 \* \* \* \*"))).to_be_visible()
    expect(page.get_by_text(re.compile(r"^(Active|Inactive)$"))).to_be_visible()


def test_execution_history_shows_success_and_failure(project_page: Page):
    page = project_page
    open_executions(page)
    expect(page.get_by_role("button", name="Export CSV")).to_be_visible()
    expect(page.get_by_text("Execution #17842")).to_be_visible()  # baseline run, 11 Oct
    expect(page.get_by_text("Execution #17970")).to_be_visible()  # failed drop-column run
    expect(page.get_by_text("Success", exact=True).first).to_be_visible()
    expect(page.get_by_text("Failure", exact=True).first).to_be_visible()
