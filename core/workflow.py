from typing import Optional
from .base import Patient, PatientContext, PatientManager
from config.rev_map.insurance_tab import InsuranceTab
from config.rev_map.patient_page import PatientPage
import uuid

class PatientWorkflow:
    def __init__(self, handler, patient: Patient, manager: PatientManager):
        self.handler = handler
        self.patient = patient
        self.manager = manager
        
        # Initialize all page handlers with the patient context
        context = PatientContext(patient=patient, session_id=str(uuid.uuid4()))
        self.insurance = InsuranceTab(handler, context)
        self.patient_page = PatientPage(handler, context)
        # Add other page handlers as needed
    
    def run_insurance_workflow(self):
        """Example workflow for insurance-related tasks"""
        try:
            # Navigate to patient
            self.patient_page.navigate_to_patient_page()
            self.patient_page.search_patient(
                first_name=self.patient.first_name,
                last_name=self.patient.last_name
            )
            
            # Handle insurance
            self.insurance.scrape_insurance()
            
            # Update patient data in manager
            self.manager.add_patient(self.patient)
            
        except Exception as e:
            self.handler.logger.log_error(f"Insurance workflow failed: {str(e)}")
            raise 