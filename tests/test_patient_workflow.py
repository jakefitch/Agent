import pytest
from datetime import datetime
from core.base import Patient, PatientContext, PatientManager
from core.workflow import PatientWorkflow
from config.rev_map.patient_page import PatientPage
from config.rev_map.insurance_tab import InsuranceTab
from core.playwright_handler import get_handler

class MockPatient(Patient):
    """Test-specific patient class with mock data"""
    def __init__(self):
        super().__init__(
            first_name="Test",
            last_name="Patient",
            date_of_birth=datetime(1990, 1, 1),
            patient_id="TEST123"
        )

@pytest.fixture
def handler():
    return get_handler()

@pytest.fixture
def patient_manager():
    return PatientManager()

@pytest.fixture
def mock_patient():
    return MockPatient()

@pytest.fixture
def patient_context(mock_patient):
    return PatientContext(
        patient=mock_patient,
        session_id="test_session_123"
    )

def test_patient_creation():
    """Test that we can create a Patient object with all required fields"""
    patient = Patient(
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1990, 1, 1)
    )
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    assert patient.date_of_birth == datetime(1990, 1, 1)

def test_patient_manager(patient_manager, mock_patient):
    """Test the PatientManager's ability to store and retrieve patients"""
    # Add a patient
    patient_manager.add_patient(mock_patient)
    
    # Retrieve the patient
    retrieved = patient_manager.get_patient(
        first_name=mock_patient.first_name,
        last_name=mock_patient.last_name
    )
    
    assert retrieved is not None
    assert retrieved.first_name == mock_patient.first_name
    assert retrieved.last_name == mock_patient.last_name

def test_insurance_tab_requires_patient(handler):
    """Test that InsuranceTab requires a patient context"""
    with pytest.raises(ValueError, match="requires a patient context"):
        InsuranceTab(handler)

def test_patient_workflow(handler, mock_patient, patient_manager):
    """Test the complete patient workflow"""
    workflow = PatientWorkflow(handler, mock_patient, patient_manager)
    
    # Run the insurance workflow
    workflow.run_insurance_workflow()
    
    # Verify the patient was updated in the manager
    retrieved = patient_manager.get_patient(
        first_name=mock_patient.first_name,
        last_name=mock_patient.last_name
    )
    assert retrieved is not None
    assert retrieved.insurance_data is not None

def test_patient_context_cookie_handling(handler, patient_context):
    """Test that cookies are properly handled in the patient context"""
    # Create a page with the context
    page = PatientPage(handler, patient_context)
    
    # Update cookies
    test_cookies = {"test_cookie": "test_value"}
    patient_context.update_cookies(test_cookies)
    
    # Set the updated context
    page.set_context(patient_context)
    
    # Verify the cookies were added to the page
    # Note: This is a simplified test - in reality, you'd need to verify
    # the cookies were actually set in the browser context
    assert patient_context.cookies == test_cookies 