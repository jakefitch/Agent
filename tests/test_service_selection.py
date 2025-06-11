import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.vsp_map.authorization_page import AuthorizationPage
from core.base import Patient
from core.logger import Logger

class DummyPage:
    pass

def build_page():
    return AuthorizationPage(DummyPage(), Logger())


def test_exam_and_contacts():
    patient = Patient(first_name="A", last_name="B")
    patient.add_claim_item(vcode="92014", description="Exam", billed_amount=1.0, code="92014")
    patient.add_claim_item(vcode="V2520", description="Contacts", billed_amount=1.0, code="V2520")

    page = build_page()
    indices = page._services_from_claims(patient)
    assert set(indices) == {0, 4}


def test_frame_and_lens():
    patient = Patient(first_name="A", last_name="B")
    patient.add_claim_item(vcode="V2020", description="Frame", billed_amount=1.0, code="V2020")
    patient.add_claim_item(vcode="V2100", description="Lens", billed_amount=1.0, code="V2100")

    page = build_page()
    indices = page._services_from_claims(patient)
    assert set(indices) == {2, 3}
