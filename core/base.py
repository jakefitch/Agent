from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
from playwright.sync_api import Page
from core.logger import Logger
import os
import time
from bs4 import BeautifulSoup
import json

@dataclass
class ClaimItem:
    """Represents a single item in a claim."""
    vcode: str
    description: str
    billed_amount: float
    code: str  # CPT or Dx code
    quantity: int = 1
    modifier: Optional[str] = None
    # Date of service for the claim item. Stored as the post date
    # scraped from the invoice details page.
    date: Optional[str] = None
    # Copay amount associated with the claim item. This is derived from
    # the "Adjustments" column on the invoice details table.
    copay: Optional[str] = None

@dataclass
class Patient:
    """A simple class to store patient data during scraping."""
    first_name: str
    last_name: str
    dob: Optional[str] = None  # Date of birth may be unavailable initially
    
    # Insurance information
    insurance_data: Dict[str, Any] = field(default_factory=dict)
    
    # Demographics
    demographics: Dict[str, Any] = field(default_factory=dict)
    
    # Medical information
    medical_data: Dict[str, Any] = field(default_factory=dict)
    
    # Claims information
    claims: List[ClaimItem] = field(default_factory=list)
    
    # Product information
    frames: Dict[str, Any] = field(default_factory=dict)
    lenses: Dict[str, Any] = field(default_factory=dict)
    contacts: Dict[str, Any] = field(default_factory=dict)

    # Flags for invoice type
    has_optical_order: bool = False
    has_frame: bool = False
    
    def __post_init__(self):
        """Convert dob string to datetime if needed"""
        if not self.dob:
            # DOB may be unknown when the patient record is first created
            self._dob_datetime = None
            return

        if isinstance(self.dob, str):
            try:
                # Try MM/DD/YYYY format first
                self._dob_datetime = datetime.strptime(self.dob, '%m/%d/%Y')
            except ValueError:
                try:
                    # Try YYYY-MM-DD format
                    self._dob_datetime = datetime.strptime(self.dob, '%Y-%m-%d')
                except ValueError:
                    raise ValueError("DOB must be in MM/DD/YYYY or YYYY-MM-DD format")
        else:
            self._dob_datetime = self.dob
    
    @property
    def date_of_birth(self) -> Optional[datetime]:
        """Get the date of birth as a datetime object if available"""
        return self._dob_datetime
    
    def add_insurance_data(self, key: str, value: Any) -> None:
        """Add insurance data to the patient record."""
        self.insurance_data[key] = value
    
    def add_demographic_data(self, key: str, value: Any) -> None:
        """Add demographic data to the patient record."""
        self.demographics[key] = value
    
    def add_medical_data(self, key: str, value: Any) -> None:
        """Add medical data to the patient record."""
        self.medical_data[key] = value
    
    def add_frame_data(self, key: str, value: Any) -> None:
        """Add frame data to the patient record."""
        self.frames[key] = value
    
    def add_lens_data(self, key: str, value: Any) -> None:
        """Add lens data to the patient record."""
        self.lenses[key] = value
    
    def add_contact_data(self, key: str, value: Any) -> None:
        """Add contact lens data to the patient record."""
        self.contacts[key] = value
    
    def add_claim_item(self, vcode: str, description: str, billed_amount: float, 
                      code: str, quantity: int = 1, modifier: Optional[str] = None) -> None:
        """Add a claim item to the patient's claims list."""
        claim_item = ClaimItem(
            vcode=vcode,
            description=description,
            billed_amount=billed_amount,
            code=code,
            quantity=quantity,
            modifier=modifier
        )
        self.claims.append(claim_item)
    
    def get_insurance_data(self, key: str) -> Optional[Any]:
        """Get insurance data by key."""
        return self.insurance_data.get(key)
    
    def get_demographic_data(self, key: str) -> Optional[Any]:
        """Get demographic data by key."""
        return self.demographics.get(key)
    
    def get_medical_data(self, key: str) -> Optional[Any]:
        """Get medical data by key."""
        return self.medical_data.get(key)
    
    def get_frame_data(self, key: str) -> Optional[Any]:
        """Get frame data by key."""
        return self.frames.get(key)
    
    def get_lens_data(self, key: str) -> Optional[Any]:
        """Get lens data by key."""
        return self.lenses.get(key)
    
    def get_contact_data(self, key: str) -> Optional[Any]:
        """Get contact lens data by key."""
        return self.contacts.get(key)
    
    def get_claims(self) -> List[ClaimItem]:
        """Get all claim items."""
        return self.claims
    
    def get_claims_by_vcode(self, vcode: str) -> List[ClaimItem]:
        """Get all claim items with a specific vcode."""
        return [claim for claim in self.claims if claim.vcode == vcode]
    
    def print_data(self) -> None:
        """Print all patient data for debugging."""
        print("\nPatient Information:")
        print(f"Name: {self.first_name} {self.last_name}")
        print(f"DOB: {self.dob}")
        
        print("\nInsurance Data:")
        for key, value in self.insurance_data.items():
            print(f"{key}: {value}")
        
        print("\nDemographics:")
        for key, value in self.demographics.items():
            print(f"{key}: {value}")
        
        print("\nMedical Data:")
        for key, value in self.medical_data.items():
            print(f"{key}: {value}")
        
        print("\nClaims:")
        for i, claim in enumerate(self.claims, 1):
            print(f"\nClaim Item {i}:")
            print(f"  VCode: {claim.vcode}")
            print(f"  Description: {claim.description}")
            print(f"  Billed Amount: ${claim.billed_amount:.2f}")
            print(f"  Code: {claim.code}")
            print(f"  Quantity: {claim.quantity}")
            if claim.modifier:
                print(f"  Modifier: {claim.modifier}")
            if claim.copay:
                print(f"  Copay: {claim.copay}")
        
        print("\nFrame Data:")
        for key, value in self.frames.items():
            print(f"{key}: {value}")
        
        print("\nLens Data:")
        for key, value in self.lenses.items():
            print(f"{key}: {value}")
        
        print("\nContact Lens Data:")
        for key, value in self.contacts.items():
            print(f"{key}: {value}")

    def to_dict(self) -> dict:
        """Convert patient data to a dictionary for easy printing/viewing."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "dob": self.dob,
            "demographics": self.demographics,
            "insurance_data": self.insurance_data,
            "medical_data": self.medical_data
        }

@dataclass
class PatientContext:
    patient: Patient
    session_id: str
    last_page: Optional[str] = None
    cookies: Optional[dict] = None
    
    def update_page(self, page_name: str):
        self.last_page = page_name
    
    def update_cookies(self, new_cookies: dict):
        self.cookies = new_cookies

class BasePage:
    def __init__(self, page: Page, logger: Logger, context: Optional[PatientContext] = None):
        self.page = page
        self.logger = logger
        self.context = context
    
    def set_context(self, context: PatientContext):
        self.context = context
        if self.context and self.context.cookies:
            self.page.context.add_cookies(self.context.cookies)
    
    def _validate_patient_required(self):
        """Warns if no patient context is available but allows execution to continue"""
        if not self.context or not getattr(self.context, 'patient', None):
            self.logger.log("WARNING: Running without patient context.")

    def get_page_soup(self) -> BeautifulSoup:
        """Get the current page's DOM as a BeautifulSoup object."""
        return BeautifulSoup(self.page.content(), 'html.parser')

    def take_screenshot(self, error_message: Optional[str] = None) -> None:
        """Take a screenshot and save it to a file.
        
        Args:
            error_message: Optional message describing the error. If not provided,
                          the screenshot will be saved with just a timestamp.
        """
        try:
            # Get screenshot path from logger
            screenshot_path = self.logger.get_screenshot_path()
            # Take screenshot
            self.page.screenshot(path=str(screenshot_path))
            if error_message:
                self.logger.log(f"Screenshot saved as {screenshot_path} for error: {error_message}")
            else:
                self.logger.log(f"Screenshot saved as {screenshot_path}")
        except Exception as e:
            self.logger.log(f"Failed to take screenshot: {str(e)}")

    def save_page_state(self, name: str) -> None:
        """Save both a screenshot and HTML soup of the current page state.
        
        Args:
            name: Base name for the saved files (without extension)
        """
        try:
            self.logger.log(f"[DEBUG] Starting save_page_state for {name}")
            
            # Create rev_map/debug folder if it doesn't exist
            debug_dir = os.path.join('config', 'debug')
            self.logger.log(f"[DEBUG] Creating debug directory: {debug_dir}")
            os.makedirs(debug_dir, exist_ok=True)
            
            # Scroll to capture full page content
            self.logger.log("[DEBUG] Scrolling to capture full page content")
            try:
                # Get page height
                page_height = self.page.evaluate("document.documentElement.scrollHeight")
                viewport_height = self.page.evaluate("window.innerHeight")
                
                # Scroll to bottom
                self.page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                # Wait for any lazy-loaded content
                self.page.wait_for_timeout(1000)
                # Scroll back to top
                self.page.evaluate("window.scrollTo(0, 0)")
                self.page.wait_for_timeout(500)
            except Exception as e:
                self.logger.log_error(f"[DEBUG] Scrolling failed: {str(e)}")
            
            # Save screenshot with timeout and error handling
            screenshot_path = os.path.join(debug_dir, f"{name}.png")
            self.logger.log(f"[DEBUG] Saving screenshot to: {screenshot_path}")
            try:
                # Try to take screenshot immediately with a short timeout
                self.logger.log("[DEBUG] Attempting immediate screenshot")
                self.page.screenshot(path=screenshot_path, timeout=3000, full_page=True)
                self.logger.log("[DEBUG] Screenshot saved successfully")
            except Exception as e:
                self.logger.log_error(f"[DEBUG] Immediate screenshot failed: {str(e)}")
                # Try alternative screenshot method
                try:
                    self.logger.log("[DEBUG] Attempting alternative screenshot method")
                    self.page.screenshot(path=screenshot_path, full_page=True, timeout=3000)
                    self.logger.log("[DEBUG] Alternative screenshot saved successfully")
                except Exception as e2:
                    self.logger.log_error(f"[DEBUG] Alternative screenshot also failed: {str(e2)}")
                    # Try one last time with a different approach
                    try:
                        self.logger.log("[DEBUG] Attempting final screenshot method")
                        # Force a small wait to let any animations settle
                        self.page.wait_for_timeout(1000)
                        self.page.screenshot(path=screenshot_path, timeout=3000)
                        self.logger.log("[DEBUG] Final screenshot attempt successful")
                    except Exception as e3:
                        self.logger.log_error(f"[DEBUG] All screenshot attempts failed: {str(e3)}")
                        self.logger.log("[DEBUG] Continuing without screenshot")
            
            # Save HTML soup
            self.logger.log("[DEBUG] Getting page soup")
            # Get the full HTML content after scrolling
            html_content = self.page.evaluate("document.documentElement.outerHTML")
            soup = BeautifulSoup(html_content, 'html.parser')
            html_path = os.path.join(debug_dir, f"{name}.html")
            self.logger.log(f"[DEBUG] Saving HTML to: {html_path}")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            self.logger.log(f"Saved page state to {debug_dir}/{name}.*")
            
        except Exception as e:
            self.logger.log_error(f"Failed to save page state: {str(e)}")
            self.logger.log_error(f"Error type: {type(e).__name__}")
            self.take_screenshot("Failed to save page state")
            raise

    def save_element_context(self, selector: str, name: str = None, context_lines: int = 5) -> Dict[str, Any]:
        """Save HTML context around a specific element when a selector fails.
        
        This function captures the HTML snippet around the target element, including
        parent and sibling elements, to help debug selector issues.
        
        Args:
            selector: The Playwright selector that failed
            name: Base name for the saved files (defaults to 'element_context')
            context_lines: Number of lines of context to capture around the element
            
        Returns:
            Dict containing the captured HTML snippet and metadata
        """
        try:
            if name is None:
                name = "element_context"
            
            self.logger.log(f"[DEBUG] Starting save_element_context for selector: {selector}")
            
            # Create debug folder if it doesn't exist
            debug_dir = os.path.join('config', 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Get the full page HTML
            html_content = self.page.evaluate("document.documentElement.outerHTML")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to find the element using the selector
            try:
                # Use JavaScript to find the element and get its context
                js_code = f"""
                (() => {{
                    try {{
                        const element = document.querySelector('{selector}');
                        if (!element) {{
                            return {{
                                found: false,
                                error: 'Element not found',
                                similar_elements: []
                            }};
                        }}
                        
                        // Get the element's outer HTML
                        const elementHTML = element.outerHTML;
                        
                        // Get parent context (up to 3 levels)
                        let parentContext = '';
                        let current = element.parentElement;
                        let level = 0;
                        while (current && level < 3) {{
                            parentContext = current.outerHTML + '\\n' + parentContext;
                            current = current.parentElement;
                            level++;
                        }}
                        
                        // Get sibling context
                        const siblings = Array.from(element.parentElement?.children || []);
                        const siblingContext = siblings.map(sibling => sibling.outerHTML).join('\\n');
                        
                        // Find similar elements (same tag name or similar attributes)
                        const similarElements = Array.from(document.querySelectorAll('*')).filter(el => {{
                            if (el === element) return false;
                            if (el.tagName === element.tagName) return true;
                            if (el.className && element.className && el.className === element.className) return true;
                            if (el.id && element.id && el.id === element.id) return true;
                            return false;
                        }}).slice(0, 5).map(el => {{
                            return {{
                                tag: el.tagName,
                                id: el.id,
                                className: el.className,
                                textContent: el.textContent?.substring(0, 100),
                                outerHTML: el.outerHTML
                            }};
                        }});
                        
                        return {{
                            found: true,
                            elementHTML: elementHTML,
                            parentContext: parentContext,
                            siblingContext: siblingContext,
                            similar_elements: similarElements,
                            elementInfo: {{
                                tag: element.tagName,
                                id: element.id,
                                className: element.className,
                                attributes: Array.from(element.attributes).map(attr => {{
                                    return {{ name: attr.name, value: attr.value }};
                                }})
                            }}
                        }};
                    }} catch (error) {{
                        return {{
                            found: false,
                            error: error.message,
                            similar_elements: []
                        }};
                    }}
                }})();
                """
                
                result = self.page.evaluate(js_code)
                
                if not result.get('found', False):
                    # Element not found, try to find similar elements
                    self.logger.log(f"[DEBUG] Element not found with selector: {selector}")
                    
                    # Create a context file with the error and similar elements
                    context_data = {
                        "timestamp": datetime.now().isoformat(),
                        "selector": selector,
                        "error": result.get('error', 'Element not found'),
                        "similar_elements": result.get('similar_elements', []),
                        "full_page_html": str(soup.prettify())[:10000]  # First 10k chars for context
                    }
                    
                    context_path = os.path.join(debug_dir, f"{name}_context.json")
                    with open(context_path, 'w', encoding='utf-8') as f:
                        json.dump(context_data, f, indent=2, ensure_ascii=False)
                    
                    self.logger.log(f"[DEBUG] Saved element context (not found) to: {context_path}")
                    return context_data
                
                # Element found, save detailed context
                context_data = {
                    "timestamp": datetime.now().isoformat(),
                    "selector": selector,
                    "found": True,
                    "element_info": result.get('elementInfo', {}),
                    "element_html": result.get('elementHTML', ''),
                    "parent_context": result.get('parentContext', ''),
                    "sibling_context": result.get('siblingContext', ''),
                    "similar_elements": result.get('similar_elements', [])
                }
                
                # Save context data
                context_path = os.path.join(debug_dir, f"{name}_context.json")
                with open(context_path, 'w', encoding='utf-8') as f:
                    json.dump(context_data, f, indent=2, ensure_ascii=False)
                
                # Save HTML snippet for easy viewing
                html_snippet = f"""
<!-- Element Context for Selector: {selector} -->
<!-- Timestamp: {context_data['timestamp']} -->

<!-- Target Element HTML: -->
{context_data['element_html']}

<!-- Parent Context: -->
{context_data['parent_context']}

<!-- Sibling Context: -->
{context_data['sibling_context']}
"""
                
                html_path = os.path.join(debug_dir, f"{name}_snippet.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_snippet)
                
                # Take a screenshot of the area around the element
                try:
                    screenshot_path = os.path.join(debug_dir, f"{name}_screenshot.png")
                    # Try to take a screenshot of the element if it's visible
                    element = self.page.locator(selector)
                    if element.is_visible(timeout=1000):
                        element.screenshot(path=screenshot_path)
                        context_data["screenshot_path"] = screenshot_path
                    else:
                        # Take full page screenshot if element not visible
                        self.page.screenshot(path=screenshot_path, full_page=True)
                        context_data["screenshot_path"] = screenshot_path
                except Exception as e:
                    self.logger.log_error(f"[DEBUG] Screenshot failed: {str(e)}")
                
                self.logger.log(f"[DEBUG] Saved element context to: {context_path}")
                self.logger.log(f"[DEBUG] Saved HTML snippet to: {html_path}")
                
                return context_data
                
            except Exception as e:
                self.logger.log_error(f"[DEBUG] Error finding element: {str(e)}")
                
                # Save error context
                error_data = {
                    "timestamp": datetime.now().isoformat(),
                    "selector": selector,
                    "error": str(e),
                    "full_page_html": str(soup.prettify())[:10000]
                }
                
                error_path = os.path.join(debug_dir, f"{name}_error.json")
                with open(error_path, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)
                
                return error_data
                
        except Exception as e:
            self.logger.log_error(f"Failed to save element context: {str(e)}")
            return {"error": str(e)}

    def save_state(self) -> None:
        """Save both a screenshot and HTML soup of the current page state using default filenames.
        
        This is a simplified version of save_page_state that uses 'state' as the base filename.
        """
        self.save_page_state("state")

    def wait_for_network_idle(self, timeout: int = 30000) -> bool:
        """Wait until the page's network activity has settled."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception as e:
            self.logger.log_error(f"Network idle wait failed: {str(e)}")
            return False

class PatientManager:
    def __init__(self):
        self._patients: Dict[str, Patient] = {}
        self._lock = Lock()
    
    def create_patient(
        self, first_name: str, last_name: str, dob: Optional[str] = None
    ) -> Patient:
        """Create a new patient and add it to the manager."""
        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            dob=dob
        )
        self.add_patient(patient)
        return patient
    
    def add_patient(self, patient: Patient) -> None:
        """Add or update a patient in the manager"""
        with self._lock:
            key = self._generate_patient_key(patient)
            self._patients[key] = patient
    
    def get_patient(self, first_name: str, last_name: str) -> Optional[Patient]:
        """Retrieve a patient by their name"""
        with self._lock:
            key = self._generate_patient_key(Patient(
                first_name=first_name,
                last_name=last_name,
                dob="01/01/2000"  # Temporary DOB for key generation
            ))
            return self._patients.get(key)
    
    def remove_patient(self, first_name: str, last_name: str) -> None:
        """Remove a patient from the manager by name"""
        with self._lock:
            key = self._generate_patient_key(Patient(
                first_name=first_name,
                last_name=last_name,
                dob="01/01/2000"  # Temporary DOB for key generation
            ))
            self._patients.pop(key, None)
    
    def get_all_patients(self) -> List[Patient]:
        """Get all patients in the manager"""
        with self._lock:
            return list(self._patients.values())
    
    @staticmethod
    def _generate_patient_key(patient: Patient) -> str:
        """Generate a unique key for a patient"""
        return f"{patient.last_name.lower()}_{patient.first_name.lower()}" 