import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(channel="chrome", headless=False)
    context = browser.new_context(service_workers="block")
    page = context.new_page()
    page.goto("https://etp.metal-it.ru/frame/index.html?loginTarget=%2Ftrades%3Fpage%3Dpurchases.trades.search")
    page.locator(".mat-form-field-infix.ng-tns-c2794762957-9").click()
    page.get_by_role("textbox", name="Логин").fill("<LOGIN>")
    page.locator(".mat-form-field-infix.ng-tns-c2794762957-10").click()
    page.get_by_role("textbox", name="Пароль").fill("<PASSWORD>")
    page.get_by_role("button", name="ДАЛЕЕ").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_role("button", name="1").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_role("button", name="1").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_role("button", name="1").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("silhouette-container").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_role("button", name="1").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("close-button").click()
    page.get_by_role("button", name="ДАЛЕЕ").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("close-button").click()
    page.get_by_role("button", name="ДАЛЕЕ").dblclick()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("close-button").click()
    page.get_by_role("button", name="ДАЛЕЕ").click()
    page.locator("[data-testid=\"advanced-iframe\"]").content_frame.get_by_test_id("close-button").click()
    page.get_by_role("button", name="ДАЛЕЕ").click()
    page.get_by_role("link", name="125133-ТТ Запчасти Epiroc").click()
    page.get_by_role("link", name="Изменить").click()
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Экспорт").click()
    download = download_info.value

    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
