
class InvoicePage:
    def __init__(self, page):
        self.page = page

    def is_loaded(self):
        return self.page.locator("#claims_table").is_visible()

    def get_results_table(self):
        return self.page.locator("#claims_table")