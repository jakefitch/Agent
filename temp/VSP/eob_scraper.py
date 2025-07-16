import pdfplumber
import re
import string

pdf_path = '/home/jake/Downloads/document.pdf'
driver = None
wait = None
actions = None


def extract_claims(pdf_path):
    data = []
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                text += page.extract_text() or ""
            except Exception as e:
                print(f"An error occurred on page {page_num}: {e}. Skipping this page.")

        claim_pattern = r"((CHOICE|SIG PLAN|ADVTG|ENHCDAD|EXAMONL)([\s\S]*?))(?=CHOICE|SIG PLAN|ADVTG|ENHCDAD|EXAMONL|$)"
        #print(text)
        matches = re.findall(claim_pattern, text, re.DOTALL)
        # Remove any match that contains the string 'In-Office Finishing Service'
        matches = [match for match in matches if 'In-Office Finishing Service' not in match[0]]
        print(f'there were {len(matches)} matches!!!!!!')

        patient_names = []
        total_billed_items = []
        for match in matches:
            patient_info = match[0].strip()
            #print(patient_info)
            lines = [line.strip() for line in patient_info.split("\n") if line.strip()]
            # Remove any lines with a Y or V or 4 as the only character
            lines = [line for line in lines if not re.match(r'^[YV]$', line)]
            ##print(lines)
            #print(lines)
            # If the line contains "TOTAL THIS OFFICE:", stop further processing
            filtered_lines = []
            for line in lines:
                if line.startswith("TOTAL THIS OFFICE:"):
                    break
                filtered_lines.append(line)

            # Replace `lines` with the filtered list
            lines = filtered_lines
            lines = [re.sub(r'\b[VY] \b', '', line) for line in lines]
            print(lines)

            # Extract date of service
            date_pattern = r"\d{1,2}/\d{1,2}/\d{2}"
            date_matches = re.findall(date_pattern, "\n".join(lines))
            date_of_service = date_matches[0] if date_matches else "Date not found"
            #print(f"Date of Service: {date_of_service}")

            #remove just th date of service and the space after it. keeping the rest of the line
            lines = [line.replace(date_of_service + " ", "") for line in lines]
    


            # Find the 'Totals' line and extract the total billed
            total_billed = "Total not found"
            try:
                for line in lines:
                    if 'Totals' in line:
                        total_parts = line.split()
                        # Assuming the last part of the line is the total billed amount
                        total_billed = total_parts[1]
                        #print(f'Total billed: {total_billed}')
                        break
            except Exception as e:
                print(f"An error occurred: {e}")

            if total_billed == "Total not found":
                print("No Total found in line, this one is getting skipped")
                break
            else:
                #do nothing
                pass

            #remove the total line
            lines = [line for line in lines if 'Totals' not in line]
            
            


            name = None

            # Iterate through the first few lines to find a line likely containing a name
            for i, candidate in enumerate(lines[:7]):  # Adjust range as needed
                match = re.search(r'([A-Z\s\-]+, [A-Z\s\-]*)', candidate)
                if match:
                    name = match.group(1).strip()
                    # Check if the name seems incomplete (e.g., ends with a comma or space)
                    if ',' in name and name.endswith(','):
                        # Look at the next line for continuation
                        next_line = lines[i + 1] if i + 1 < len(lines) else ''
                        name += f" {next_line.split()[0]}"  # Add the first word from the next line

                        
                    break

                else:
                    print(f'no name found in {candidate}')

            #if the last name has a letter followed by a spacc to start, pop the letter and the space off
            if len(name) > 2 and name[1] == ' ' and name[0] in string.ascii_letters:
                print(f"Popping off the first letter and space from: {name}")
                name = name[2:]  # Remove the first two characters
                print(f"New name is: {name}")

            print(f"Name found: {name}")
                    #if no name is found, skip the iteration
            if name is None:
                print(f"No name found in: {candidate}")
                if i + 1 < len(lines):
                    print(f"Next line: {lines[i + 1]}")

            #remove the line with he name in it
            
            lines = [line for line in lines if name not in line]
            

            # remove any lines that start with 'VSP Vision Care'
            lines = [line for line in lines if not line.startswith('VSP Vision Care')]
            # remove any lines that start with '1320' or 'Plan' or 'Number' or 'Total' or 'Proc' or 'Service
            remove_list = ['1320', 'Plan', 'Number', 'Total', 'Proc', 'Service']
            lines = [line for line in lines if not any(word in line for word in remove_list)]
            #remove any lines that contain a 4 digit number
            lines = [line for line in lines if not re.match(r'^\d{4}$', line)]
            
            #if the line contains "TOTAL THIS OFFICE:" then we've reached the end of the items we want to extract. we shouldn't count any more lines
            
            
            
            
            #print(lines)

            # Define a dictionary for replacements
            replacements = {
                "JA": "V2781", "JH": "V2783", "QT": "V2750", "AD": "V2784", "JD": "V2784",
                "PR": "V2744", "DD": "V2784", "DA": "V2762", "QV": "V2750", "QR": "V2761",
                "MN": "V2745", "QM": "V2750", "BV": "V2755", "AH": "V2783", "SW": "V2020",
                "BA": "V2799", "RM": "V2799", "TA": "V2744", "BD": "V2799", "FA": "V2781",
                "FH": "V2783", "OA": "V2781", "OD": "V2784", "LF": "V2783", "OH":  "V2783",
                "Variable": "V2781"# LF may not be set correctly?
            }

            # Replace specific substrings in lines
            lines = [
                ' '.join(replacements.get(word, word) for word in line.split())
                for line in lines
            ]
            print("Lines after replacements:", lines)

            merged_items = {}

            for item in lines:
                # Assuming `item` is a string, split it into parts
                parts = item.split()  # Splits the string into a list of words/numbers

                # Updated function to check if a value looks like currency (positive or negative)
                def is_currency(value):
                    return re.match(r'^-?\d+\.\d{2}$', value) is not None

                # Check if the first item is '1' or '2'
                if parts and parts[0] in ['1', '2']:
                    for i, part in enumerate(parts[1:], start=1):  # Start checking from the second item
                        #if the part starts with a V or Y followed by a space, remove the V/Y and the space
                        if part.startswith('V ') or part.startswith('Y '):
                            parts[i] = part[2:]
                        if part.startswith('V') or part.startswith('Y'):  # Look for an item starting with 'V' or 'Y'
                            # Move the item starting with 'V' or 'Y' to the first place
                            parts.insert(0, parts.pop(i))
                            break  # Stop once the first 'V' or 'Y' item is moved
                    #print(f"Reordered parts: {parts}")
                
                
                # Remove items until a currency-like value is found
                while parts and not is_currency(parts[-1]):
                    parts.pop()

                # If a currency value is found, it will be the last item
                if parts:
                    price = parts[-1]
                    #print(f"Currency value found: {price}")
                else:
                    #print("No currency value found.")
                    pass

                #if a date value is found in the parts, remove it
                for i, part in enumerate(parts):
                    if re.match(r'\d{1,2}/\d{1,2}/\d{2}', part):
                        parts.pop(i)
                        break
                
                # Print the result
                print(f'Parts after processing: {parts}')

                
        
                
                        

                
                
                
                
                
                #if the list parts is empty, skip the iteration
                if not parts:
                    continue
                code = parts[0]  # First item in the split list
                value = parts[-1]
                #code = parts[0]  # First item in the split list
                #the value is the last part of the list that looks like a price (contains .xx)
                #value = parts[-1]
                
                # Print the extracted values
                #print(f"Code: {code}, Value: {value}")

                if code in merged_items:
                    # Convert existing value and current value to float, sum them, and store as a string
                    merged_items[code] = str(float(merged_items[code]) + float(value))
                else:
                    # Store the value as a string, but ensure it's initially treated as a float
                    merged_items[code] = str(float(value))

                            
                aggregated_items_list = [[code, str(value)] for code, value in merged_items.items()]
                print(f'billed item list = {aggregated_items_list}')

            patient_names.append(name)
            total_billed_items.append(total_billed)
            data.append((name, date_of_service, aggregated_items_list, total_billed))
            
            print("------------------------------------")
            print(f"Name: {name}")
            print(f"Date of Service: {date_of_service}")
            print(f"Items: {aggregated_items_list}")
            #total the payments from the aggregated items by adding the float values
            total_posted = sum(float(item[1]) for item in aggregated_items_list)
            print(f'Total Posted: {total_posted}')
            print(f"Total Billed: {total_billed}")
            #provider payment is the float total of the aggregated items
            total_paid = sum(float(item[1]) for item in aggregated_items_list)
            print(f"Total Paid: {total_paid}")
            print(' ')

    return data

eob_data = extract_claims(pdf_path)
#print the total paid. this is teh float total of the aggregated items for all patients
# Calculate total paid for all patients
total_paid = sum(
    sum(float(item[1]) for item in patient[2])  # Sum of items for each patient
    for patient in eob_data                    # Iterate through all patients
)




print(f'Total Paid: {total_paid}')
          