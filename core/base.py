from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
from playwright.sync_api import Page
from core.logger import Logger
import os
import time
from bs4 import BeautifulSoup

@dataclass
class ClaimItem:
    """Represents a single item in a claim."""
    vcode: str
    description: str
    billed_amount: float
    code: str  # CPT or Dx code
    quantity: int = 1
    modifier: Optional[str] = None

@dataclass
class Patient:
    """A simple class to store patient data during scraping."""
    first_name: str
    last_name: str
    dob: str  # Changed from date_of_birth: datetime to dob: str
    
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
    
    def __post_init__(self):
        """Convert dob string to datetime if needed"""
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
    def date_of_birth(self) -> datetime:
        """Get the date of birth as a datetime object"""
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
            # Create rev_map/debug folder if it doesn't exist
            debug_dir = os.path.join('config', 'rev_map', 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Save screenshot
            screenshot_path = os.path.join(debug_dir, f"{name}.png")
            self.page.screenshot(path=screenshot_path)
            
            # Save HTML soup
            soup = self.get_page_soup()
            html_path = os.path.join(debug_dir, f"{name}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            
            self.logger.log(f"Saved page state to {debug_dir}/{name}.*")
            
        except Exception as e:
            self.logger.log_error(f"Failed to save page state: {str(e)}")
            raise

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
    
    def create_patient(self, first_name: str, last_name: str, dob: str) -> Patient:
        """Create a new patient and add it to the manager"""
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