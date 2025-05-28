from typing import Optional
from .base import Patient, PatientContext, PatientManager
from config.rev_map.insurance_tab import InsuranceTab
from config.rev_map.patient_page import PatientPage
import uuid

class PatientWorkflow:
    def __init__(self, handler, manager: PatientManager):
        self.handler = handler
        self.manager = manager
        self.patient = None
        self.context = None
        
        # Initialize page handlers without patient context
        self.insurance = InsuranceTab(handler)
        self.patient_page = PatientPage(handler)
    
    def set_patient(self, patient: Patient):
        """Set or update the current patient and create a new context"""
        self.patient = patient
        self.context = PatientContext(patient=patient, session_id=str(uuid.uuid4()))
        
        # Update contexts for all page handlers
        self.insurance.set_context(self.context)
        self.patient_page.set_context(self.context)
    
    def run_insurance_workflow(self):
        """Example workflow for insurance-related tasks"""
        try:
            if not self.patient:
                self.handler.logger.log("WARNING: No patient set for insurance workflow")
                return
                
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