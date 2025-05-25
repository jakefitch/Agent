from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock

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
    date_of_birth: datetime
    
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
        print(f"DOB: {self.date_of_birth}")
        
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
    def __init__(self, handler, context: Optional[PatientContext] = None):
        self.handler = handler
        self.context = context
        self._validate_patient_required()
    
    def set_context(self, context: PatientContext):
        self.context = context
        if self.context.cookies:
            self.handler.page.context.add_cookies(self.context.cookies)
        self._validate_patient_required()
    
    def _validate_patient_required(self):
        """Override this method in subclasses that require a patient"""
        pass

class PatientManager:
    def __init__(self):
        self._patients: Dict[str, Patient] = {}
        self._lock = Lock()
    
    def add_patient(self, patient: Patient) -> None:
        """Add or update a patient in the manager"""
        with self._lock:
            key = self._generate_patient_key(patient)
            self._patients[key] = patient
    
    def get_patient(self, first_name: str, last_name: str, patient_id: Optional[str] = None) -> Optional[Patient]:
        """Retrieve a patient by their identifying information"""
        with self._lock:
            key = self._generate_patient_key(Patient(first_name=first_name, last_name=last_name, patient_id=patient_id))
            return self._patients.get(key)
    
    def remove_patient(self, patient: Patient) -> None:
        """Remove a patient from the manager"""
        with self._lock:
            key = self._generate_patient_key(patient)
            self._patients.pop(key, None)
    
    @staticmethod
    def _generate_patient_key(patient: Patient) -> str:
        """Generate a unique key for a patient"""
        if patient.patient_id:
            return f"id_{patient.patient_id}"
        return f"name_{patient.first_name.lower()}_{patient.last_name.lower()}" 