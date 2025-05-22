class PageManager:
    def __init__(self, handler):
        self.handler = handler
        self._pages = {}
    
    def __getattr__(self, name):
        """Dynamically create and return page objects when accessed"""
        if name not in self._pages:
            if name == 'invoice_page':
                from config.rev_map.invoice_page import InvoicePage
                self._pages[name] = InvoicePage(self.handler)
            elif name == 'patient_page':
                from config.rev_map.patient_page import PatientPage
                self._pages[name] = PatientPage(self.handler)
            elif name == 'insurance_tab':
                from config.rev_map.insurance_tab import InsuranceTab
                self._pages[name] = InsuranceTab(self.handler)
            # Add other page imports here as needed
            # elif name == 'claims_page':
            #     from core.claims_page import ClaimsPage
            #     self._pages[name] = ClaimsPage(self.handler)
            else:
                raise AttributeError(f"Page '{name}' not found")
        return self._pages[name]
    
    def get_available_pages(self):
        """Return a list of available page objects"""
        return list(self._pages.keys()) 