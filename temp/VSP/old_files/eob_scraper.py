
import PyPDF2
import re

pdf_path = '/home/jake/Downloads/document.pdf'
driver = None
wait = None
actions = None


joined_pdf_path = 'joined.pdf'


def join_pages(pdf_path):
    writer = PyPDF2.PdfWriter()

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            writer.add_page(page)

    output_path = 'joined.pdf'

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return output_path

import pdfplumber
def extract_claims(joined_pdf_path):
    data = []
    text = ""
    

    with open(joined_pdf_path, 'rb') as file:

        reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(reader.pages):
            try:
                text += page.extract_text()
            except KeyError as e:
                print(f"KeyError: {e} on page {page_num}. Skipping this page.")
            except Exception as e:
                print(f"An error occurred on page {page_num}: {e}. Skipping this page.")
 
        claim_pattern = r"((CHOICE|SIG PLAN|ADVTG|ENHCDAD|EXAMONL)([\s\S]*?))(?=CHOICE|SIG PLAN|ADVTG|ENHCDAD|EXAMONL|$)"

        matches = re.findall(claim_pattern, text, re.DOTALL)
        #remove any match that contains the string 'In-Office Finishing Service 
        matches = [match for match in matches if 'In-Office Finishing Service' not in match[0]]
        print(f'there were {len(matches)} matches!!!!!!')
        

        

        patient_names = []
        total_billed_items = []
        for match in matches:
            patient_info = match[0].strip()
            
            
            lines = [line.strip() for line in patient_info.split("\n") if line.strip()]
            #remove any lines with with a Y or V or 4 as the only character
            lines = [line for line in lines if not re.match(r'^[YV]$', line)]

            
            date_pattern = r"\d{1,2}/\d{1,2}/\d{2}"
            date_matches = re.findall(date_pattern, patient_info)
            date_of_service = date_matches[0] if date_matches else "Date not found"

            try:
                totals_index = lines.index('Totals')
                totals_index = totals_index + 1
                total_billed = lines[totals_index]
            except:
                print("no Total found in line, this one is getting skpped")
                break
        
        
            

            name = (lines[:7])
            print(name)
            #if the third item in the name list is a number, then the name is in the 4th item
            '''if re.match(r'^\d{1,3}$', name[2]):
                name = (name[3])
            else:
                name = (name[2])'''
            
            #if the third item in the name list does not contain a letter, then the name is in the 4th item
            if not re.search(r'[a-zA-Z]', name[2]):
                name = (name[3])
            else:
                name = (name[2])
           
            print(name)
            
            for i, line in enumerate(lines):
                if "JA" in line:
                    lines[i] = "V2781"
                elif 'JH' in line:
                    lines[i] = "V2783"
                elif 'QT' in line:
                    lines[i] = "V2750"
                elif 'AD' in line:
                    lines[i] = "V2784"
                elif 'JD' in line:
                    lines[i] = "V2784"
                elif 'PR' in line:
                    lines[i] = "V2744"
                elif 'DD' in line:
                    lines[i] = 'V2784'
                elif 'DA' in line:
                    lines[i] = 'V2762'
                elif 'QV' in line:
                    lines[i] = 'V2750'
                elif 'QR' in line:
                    lines[i] = "V2761"
                elif 'MN' in line:
                    lines[i] = "V2745"
                elif 'QM' in line:
                    lines[i] = "V2750"
                elif "BV" in line:
                    lines[i] = "V2755"
                elif "AH" in line:
                    lines[i] = "V2783"
                elif "SW" in line:
                    lines[i] = "V2020"
                elif "BA" in line:
                    lines[i] = "V2799" #for digital aspheric lens, need to verify Vcode
                elif "RM" in line:
                    lines[i] = "V2799" #for oversized lens, need to verify Vcode
                elif "TA" in line:  
                    lines[i] = "V2744" #for technical addon, need to verify Vcode
                elif "BD" in line:
                    lines[i] = "V2799" #for digital asph addon, need to verify Vcode
                
    
            billed_items = []
            current_item = []


            for line in lines:
                if line.startswith(("V2", "v2")) or line.startswith('Cov') or (re.match(r"^9\d{4}$", line)):
                    if current_item:
                        billed_items.append(current_item[:9])
                    current_item = [line]
                else:
                    current_item.append(line)
            

            if current_item:
                billed_items.append(current_item)
            
            # Remove lines that start with "CHOICE" or "SIG PLAN"
            billed_items = [item for item in billed_items if not item[0].startswith(("CHOICE", "SIG PLAN"))]
            
            
            modified_items = []
            for item in billed_items:
                if len(item) >= 2 and isinstance(item[1], str) and item[1] == "0.00":
                    modified_item = [item[0], item[6]]
                    modified_items.append(modified_item)
                elif len(item) >= 2 and isinstance(item[1], str) and re.match(r'^\d{1,3}$', item[1]):
                    #try this or skip it if it doesn't work
                    try:
                        modified_item = [item[0], item[8]]
                        modified_items.append(modified_item)
                    except:
                        continue
                else:
                    continue
            
            merged_items = {}
            for item in modified_items:
                code = item[0]
                value = float(item[1])
                if code in merged_items:
                    merged_items[code] += value
                else:
                    merged_items[code] = value
            
       
            # Print the merged items
                for code, value in merged_items.items():
                    modified_item = [code, str(value)]

            
            aggregated_items_list = [[code, str(value)] for code, value in merged_items.items()]
            # Append patient name to the list
            patient_names.append(name)
            total_billed_items.append(totals_index)
            data.append((name, date_of_service, aggregated_items_list, total_billed))
   
    return data
  


eob_data = extract_claims(joined_pdf_path)
#print(eob_data)