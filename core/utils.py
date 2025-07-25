"""Utility functions for the application."""

from typing import Any, Dict, List, Optional
import re
from datetime import datetime
from core.base import Patient, ClaimItem
from bs4 import BeautifulSoup

def format_currency(amount: float) -> str:
    """Format a float amount as a currency string.
    
    Args:
        amount: The amount to format
        
    Returns:
        str: The formatted currency string (e.g., "$123.45")
    """
    return f"${amount:.2f}"

def parse_currency(currency_str: str) -> float:
    """Parse a currency string into a float.
    
    Args:
        currency_str: The currency string to parse (e.g., "$123.45")
        
    Returns:
        float: The parsed amount
    """
    return float(currency_str.strip('$').replace(',', ''))

def format_date(date_str: str, input_format: str = "%m/%d/%Y", output_format: str = "%Y-%m-%d") -> str:
    """Format a date string from one format to another.
    
    Args:
        date_str: The date string to format
        input_format: The format of the input date string
        output_format: The desired output format
        
    Returns:
        str: The formatted date string
    """
    date_obj = datetime.strptime(date_str, input_format)
    return date_obj.strftime(output_format)

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters.
    
    Args:
        text: The text to clean
        
    Returns:
        str: The cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    return text.strip()

def set_copay(patient: Patient) -> None:
    """Calculate and set the copay amount for a patient based on their claims.
    
    This function:
    1. Skips copay calculation for optical invoices (V21/V22 codes)
    2. Only considers copays for exams (9200/9201) and contacts (V25)
    3. Stores the total copay in patient.claims['copay']
    
    Args:
        patient: Patient object containing claims to process
    """
    # Initialize copay
    total_copay = 0.00
    
    # Check if this is an optical invoice
    for claim in patient.claims:
        if claim.code.startswith('V21') or claim.code.startswith('V22'):
            # This is an optical invoice, no copay needed
            patient.claims['copay'] = format_currency(0.00)
            return
    
    # Process copays for exams and contacts
    for claim in patient.claims:
        if (claim.code.startswith('9201') or 
            claim.code.startswith('9200') or 
            claim.code.startswith('V25')):
            
            # Get copay amount from the claim
            if hasattr(claim, 'copay') and claim.copay:
                copay_amount = parse_currency(claim.copay)
                total_copay += copay_amount
    
    # Store the formatted copay amount
    patient.claims['copay'] = format_currency(total_copay)

def has_glasses_order(patient: Patient) -> bool:
    """Check if a patient has any claims indicating a glasses order.

    The check is case-insensitive and looks for base lens codes such as
    ``V21xx``, ``V22xx``, ``V23xx`` or the specific ``V2781`` code.

    Args:
        patient: Patient object containing claims to check

    Returns:
        bool: True if a glasses order is found, False otherwise
    """
    if not hasattr(patient, 'claims') or not patient.claims:
        return False

    pattern = re.compile(r"^v(?:21\d\d|22\d\d|23\d\d|2781)$", re.IGNORECASE)
    for claim in patient.claims:
        if claim.code and pattern.match(claim.code.strip()):
            return True

    return False

def has_frame_claim(patient: Patient) -> bool:
    """Check if the patient has a frame claim by looking for the V2020 code.

    Args:
        patient: Patient object containing claims data

    Returns:
        bool: True if a frame claim is found, False otherwise
    """
    if not patient.claims:
        return False

    for claim in patient.claims:
        if claim.code and claim.code.strip().upper() == 'V2020':
            return True

    return False

def get_claim_service_flags(patient: Patient) -> Dict[str, bool]:
    """Return boolean flags for the types of services found in ``patient.claims``.

    The flags correspond to the categories used for VSP authorizations and claim
    submission:

    ``exam`` -- Comprehensive or medical eye exams
    ``contact_service`` -- Contact lens fitting/services
    ``lens`` -- Ophthalmic lenses
    ``frame`` -- Frame materials
    ``contacts`` -- Contact lens materials

    Args:
        patient: ``Patient`` instance containing claim items.

    Returns:
        Dictionary mapping each category name to ``True`` if a matching claim was
        found, otherwise ``False``.
    """

    flags = {
        "exam": False,
        "contact_service": False,
        "lens": False,
        "frame": False,
        "contacts": False,
    }

    if not patient.claims:
        return flags

    for claim in patient.claims:
        code = (claim.vcode or claim.code or "").upper()

        # Exam codes (92004/92014, 99xxx, S062x, S602x)
        if code in {"92004", "92014"} or code.startswith("99") or \
           code.startswith("S062") or code.startswith("S602"):
            flags["exam"] = True

        # Contact lens material codes
        if code.startswith("V252"):
            flags["contacts"] = True

        # Frame codes
        if code in {"V2020", "V2025"}:
            flags["frame"] = True

        # Lens codes
        if code.startswith(("V21", "V22", "V23")) or code.startswith("V2781"):
            flags["lens"] = True

        # Contact lens service codes
        if code.startswith("9231"):
            flags["contact_service"] = True

    return flags

def get_page_soup(page) -> BeautifulSoup:
    """Get the current page's DOM as a BeautifulSoup object."""
    return BeautifulSoup(page.content(), 'html.parser')


