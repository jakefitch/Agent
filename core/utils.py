"""Utility functions for the application."""

from typing import Any, Dict, List, Optional
import re
from datetime import datetime
from core.base import Patient, ClaimItem

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


