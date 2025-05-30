from playwright.sync_api import sync_playwright

def test_playwright():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com")
    print("Page title:", page.title())
    browser.close()
    p.stop()

if __name__ == "__main__":
    test_playwright()
