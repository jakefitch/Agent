#!/usr/bin/env python3
import pdfplumber
import os
import json
import re
from datetime import datetime

def separate_claims(full_text):
    """
    Separate the full text into individual claims.
    """
    claims = full_text.split("Claim Information")
    return claims

def extract_all_data(pdf_path):
    """
    Extract text from every page in the PDF and combine it into a single string.
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Number of pages in {pdf_path}: {len(pdf.pages)}")
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            full_text += page_text + "\n"  # add a newline to separate pages
    return full_text

def debug_claim_structure(claim_text):
    """
    Debug function to see the actual structure of claim data.
    """
    print("\n🔍 DEBUG: Claim structure analysis:")
    print("=" * 50)
    
    lines = claim_text.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Show first 20 lines to understand structure
    print("\nFirst 20 lines:")
    for i, line in enumerate(lines[:20]):
        print(f"{i:2d}: {line}")
    
    # Look for key patterns
    print("\n🔍 Looking for key patterns:")
    for i, line in enumerate(lines):
        line = line.strip()
        if any(keyword in line for keyword in ["Patient Name:", "Claim ID:", "Service Line", "Begin", "End", "SERVICE LINE TOTALS", "Patient:", "Member:", "Insured:", "Claim:", "Provider:", "Date:", "Amount:", "Code:", "NPI:"]):
            print(f"Line {i}: {line}")

def parse_claim_to_json(claim_text):
    """
    Parse a single claim text into structured JSON format.
    
    Args:
        claim_text: Raw text of a single claim
        
    Returns:
        Dictionary containing structured claim data
    """
    claim_data = {
        "patient_info": {},
        "claim_info": {},
        "service_lines": [],
        "totals": {}
    }
    
    lines = claim_text.split('\n')
    
    # Skip if this is just header information (no patient name)
    has_patient_info = any("Patient Name:" in line for line in lines)
    if not has_patient_info:
        return None
    
    # Parse patient and claim header information
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Patient information - more flexible matching
        if "Patient Name:" in line:
            parts = line.split("Patient Name:")
            if len(parts) > 1:
                patient_part = parts[1]
                # Extract patient name before any other field
                if "Member Identification" in patient_part:
                    claim_data["patient_info"]["patient_name"] = patient_part.split("Member Identification")[0].strip()
                else:
                    claim_data["patient_info"]["patient_name"] = patient_part.strip()
                    
        elif "Member Identification #:" in line:
            parts = line.split("Member Identification #:")
            if len(parts) > 1:
                member_part = parts[1]
                if "Insured Name" in member_part:
                    claim_data["patient_info"]["member_id"] = member_part.split("Insured Name")[0].strip()
                else:
                    claim_data["patient_info"]["member_id"] = member_part.strip()
                    
        elif "Insured Name:" in line:
            parts = line.split("Insured Name:")
            if len(parts) > 1:
                insured_part = parts[1]
                if "Insured Member Identification" in insured_part:
                    claim_data["patient_info"]["insured_name"] = insured_part.split("Insured Member Identification")[0].strip()
                else:
                    claim_data["patient_info"]["insured_name"] = insured_part.strip()
                    
        elif "Insured Member Identification:" in line:
            parts = line.split("Insured Member Identification:")
            if len(parts) > 1:
                member_part = parts[1]
                if "Claim ID" in member_part:
                    claim_data["patient_info"]["insured_member_id"] = member_part.split("Claim ID")[0].strip()
                else:
                    claim_data["patient_info"]["insured_member_id"] = member_part.strip()
            
        # Claim information - more flexible matching
        elif "Claim ID:" in line:
            parts = line.split("Claim ID:")
            if len(parts) > 1:
                claim_part = parts[1]
                if "Patient Account Number" in claim_part:
                    claim_data["claim_info"]["claim_id"] = claim_part.split("Patient Account Number")[0].strip()
                else:
                    claim_data["claim_info"]["claim_id"] = claim_part.strip()
                    
        elif "Patient Account Number:" in line:
            parts = line.split("Patient Account Number:")
            if len(parts) > 1:
                account_part = parts[1]
                if "Claim Status" in account_part:
                    claim_data["claim_info"]["patient_account_number"] = account_part.split("Claim Status")[0].strip()
                else:
                    claim_data["claim_info"]["patient_account_number"] = account_part.strip()
                    
        elif "Claim Status:" in line:
            parts = line.split("Claim Status:")
            if len(parts) > 1:
                status_part = parts[1]
                if "Rendering Provider" in status_part:
                    claim_data["claim_info"]["claim_status"] = status_part.split("Rendering Provider")[0].strip()
                else:
                    claim_data["claim_info"]["claim_status"] = status_part.strip()
                    
        elif "Rendering Provider:" in line:
            parts = line.split("Rendering Provider:")
            if len(parts) > 1:
                provider_part = parts[1]
                if "Rendering NPI" in provider_part:
                    claim_data["claim_info"]["rendering_provider"] = provider_part.split("Rendering NPI")[0].strip()
                else:
                    claim_data["claim_info"]["rendering_provider"] = provider_part.strip()
                    
        elif "Rendering NPI:" in line:
            parts = line.split("Rendering NPI:")
            if len(parts) > 1:
                npi_part = parts[1]
                if "Claim Payment Amount" in npi_part:
                    claim_data["claim_info"]["rendering_npi"] = npi_part.split("Claim Payment Amount")[0].strip()
                else:
                    claim_data["claim_info"]["rendering_npi"] = npi_part.strip()
                    
        elif "Claim Payment Amount:" in line:
            parts = line.split("Claim Payment Amount:")
            if len(parts) > 1:
                payment_part = parts[1]
                if "Claim Adj Amt" in payment_part:
                    claim_data["claim_info"]["claim_payment_amount"] = payment_part.split("Claim Adj Amt")[0].strip()
                else:
                    claim_data["claim_info"]["claim_payment_amount"] = payment_part.strip()
                    
        elif "Payer Claim Control # / ICN#:" in line:
            parts = line.split("Payer Claim Control # / ICN#:")
            if len(parts) > 1:
                control_part = parts[1]
                if "Patient Responsibility" in control_part:
                    claim_data["claim_info"]["payer_claim_control"] = control_part.split("Patient Responsibility")[0].strip()
                else:
                    claim_data["claim_info"]["payer_claim_control"] = control_part.strip()
                    
        elif "Patient Responsibility:" in line:
            parts = line.split("Patient Responsibility:")
            if len(parts) > 1:
                resp_part = parts[1]
                if "Patient Responsibility Reason Code" in resp_part:
                    claim_data["claim_info"]["patient_responsibility"] = resp_part.split("Patient Responsibility Reason Code")[0].strip()
                else:
                    claim_data["claim_info"]["patient_responsibility"] = resp_part.strip()
    
    # Parse service line items - look for date patterns
    service_lines_started = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for service line header
        if "Service Line Information" in line:
            service_lines_started = True
            continue
            
        # Parse service line items - look for date pattern MM/DD/YYYY
        if service_lines_started and re.match(r'\d{1,2}/\d{1,2}/\d{4}', line):
            # This is a service line item
            service_line = parse_service_line(line)
            if service_line:
                claim_data["service_lines"].append(service_line)
                
        # Look for totals
        elif "SERVICE LINE TOTALS:" in line:
            totals = parse_totals_line(line)
            if totals:
                claim_data["totals"] = totals
                break
    
    return claim_data

def parse_service_line(line):
    """
    Parse a single service line into structured data.
    
    Args:
        line: Raw service line text
        
    Returns:
        Dictionary containing service line data
    """
    # Split by spaces
    parts = line.split()
    
    # There should be at least 14 columns for a valid service line
    if len(parts) < 14:
        return None
    try:
        service_line = {
            "begin_date": parts[0],
            "end_date": parts[1],
            "rendering_npi": parts[2],
            "units": parts[3],
            "procedure_code": parts[4],
            "billed_amount": extract_amount(parts[5]),
            "allowed_amount": extract_amount(parts[6]),
            "deductible_amount": extract_amount(parts[7]),
            "coinsurance_amount": extract_amount(parts[8]),
            "copay_amount": extract_amount(parts[9]),
            "late_filing_red": extract_amount(parts[10]),
            "other_adjustments": extract_amount(parts[11]),
            "adjust_codes": parts[12],
            "provider_paid": extract_amount(parts[13]),
            "remark_codes": parts[14]
        }
        return service_line
    except (IndexError, ValueError):
        return None

def parse_totals_line(line):
    """
    Parse the totals line into structured data.
    
    Args:
        line: Raw totals line text
        
    Returns:
        Dictionary containing totals data
    """
    try:
        # Extract amounts from the totals line
        amounts = re.findall(r'\$[\d,]+\.?\d*', line)
        
        if len(amounts) >= 6:
            return {
                "total_billed": amounts[0],
                "total_allowed": amounts[1],
                "total_deductible": amounts[2],
                "total_coinsurance": amounts[3],
                "total_copay": amounts[4],
                "total_other_adjustments": amounts[5],
                "total_paid": amounts[6] if len(amounts) > 6 else "$0.00"
            }
    except:
        pass
    
    return None

def extract_amount(amount_str):
    """
    Extract and clean amount values.
    
    Args:
        amount_str: Raw amount string
        
    Returns:
        Cleaned amount string
    """
    if not amount_str or amount_str == "$0.00":
        return "$0.00"
    
    # Remove any non-numeric characters except decimal point and dollar sign
    cleaned = re.sub(r'[^\d.$]', '', amount_str)
    
    # Ensure it starts with $
    if not cleaned.startswith('$'):
        cleaned = '$' + cleaned
        
    return cleaned

def parse_all_claims_to_json(claims):
    """
    Parse all claims into JSON format.
    
    Args:
        claims: List of raw claim texts
        
    Returns:
        List of structured claim data
    """
    structured_claims = []
    
    for i, claim_text in enumerate(claims):
        if not claim_text.strip():
            continue
            
        print(f"Parsing claim {i+1}...")
        
        # Debug the first few claims to see their structure
        if i < 3:
            debug_claim_structure(claim_text)
        
        claim_json = parse_claim_to_json(claim_text)
        if claim_json:
            structured_claims.append({
                "claim_number": i+1,
                "data": claim_json
            })
    
    return structured_claims

def main():
    # Set pdf file path to era.pdf inside this directory
    pdf_file = os.path.join(os.path.dirname(__file__), "era.pdf")
    
    # Extract all data into one variable
    all_data = extract_all_data(pdf_file)
    claims = separate_claims(all_data)
    
    # Print out everything; you can then start parsing as you see fit.
    print("Extracted full data:")
    print(f'there are {len(claims)} claims')
    
    # Parse claims into structured JSON
    structured_claims = parse_all_claims_to_json(claims)
    
    # Save structured data to JSON file
    output_file = os.path.join(os.path.dirname(__file__), "structured_claims.json")
    with open(output_file, 'w') as f:
        json.dump(structured_claims, f, indent=2)
    
    print(f"✅ Structured data saved to: {output_file}")
    
    # Print first claim as example
    if structured_claims:
        print("\n📋 Example of structured claim data:")
        print(json.dumps(structured_claims, indent=2))

if __name__ == "__main__":
    main()
