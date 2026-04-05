"""Example E2E test scenarios using Playwright."""

import pytest


@pytest.mark.e2e
@pytest.mark.critical_path
async def test_user_login_success(web_page):
    """
    Scenario: User logs in successfully

    Given: User is on login page
    When: User enters valid credentials
    Then: Redirected to dashboard
    """
    # Step 1: Navigate to login
    await web_page.goto("/login")

    # Step 2: Fill email field
    await web_page.fill("input[name=email]", "user@example.com")

    # Step 3: Fill password field
    await web_page.fill("input[name=password]", "password123")

    # Step 4: Click submit button
    await web_page.click("button[type=submit]")

    # Step 5: Wait for redirect (dashboard appears)
    await web_page.wait_for_element("h1:has-text('Dashboard')")

    # Step 6: Verify success (no console errors, text present)
    await web_page.verify_success_state(expected_text="Dashboard")


@pytest.mark.e2e
async def test_user_login_invalid_credentials(web_page):
    """
    Scenario: User login fails with invalid credentials

    Given: User is on login page
    When: User enters invalid credentials
    Then: Error message appears
    """
    await web_page.goto("/login")
    await web_page.fill("input[name=email]", "invalid@example.com")
    await web_page.fill("input[name=password]", "wrong")
    await web_page.click("button[type=submit]")

    # Wait for error message
    await web_page.wait_for_element(".error-message")
    error_text = await web_page.text_content(".error-message")
    assert "Invalid" in error_text or "incorrect" in error_text.lower()


@pytest.mark.e2e
@pytest.mark.critical_path
async def test_form_submission(web_page):
    """
    Scenario: User submits form and sees confirmation
    """
    await web_page.goto("/create-project")
    await web_page.fill("input[name=project_name]", "My Project")
    await web_page.fill("textarea[name=description]", "Test project description")
    await web_page.click("button:has-text('Create')")

    # Wait for confirmation
    await web_page.wait_for_element(".success-banner")
    await web_page.verify_success_state(expected_text="Project created")


@pytest.mark.e2e
async def test_modal_interaction(web_page):
    """
    Scenario: User opens and closes modal dialog
    """
    await web_page.goto("/projects")
    await web_page.click("button:has-text('New Project')")

    # Wait for modal to appear
    await web_page.wait_for_element("[role=dialog]")
    assert await web_page.is_visible("[role=dialog]")

    # Close modal by clicking cancel
    await web_page.click("button:has-text('Cancel')")

    # Modal should disappear (wait a bit)
    await web_page.page.wait_for_timeout(500)


@pytest.mark.e2e
async def test_pagination(web_page):
    """
    Scenario: User navigates paginated list
    """
    await web_page.goto("/projects")

    # Get first page count
    first_page_text = await web_page.text_content(".project-count")
    assert first_page_text

    # Click next button
    await web_page.click("button:has-text('Next')")

    # Wait for new content
    await web_page.page.wait_for_load_state("networkidle")

    # Verify different content
    second_page_text = await web_page.text_content(".project-count")
    assert second_page_text != first_page_text
