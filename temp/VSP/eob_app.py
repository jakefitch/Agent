from my_classes import MyAutomation
import tkinter as tk
from rev_functions import loop_rows
from eob_scraper import extract_claims
from rev_functions import print_remaining_items



automation = MyAutomation("Amarillo")
automation.load_pages_vsp()
pdf_path = '/home/jake/Downloads/document.pdf'
root = tk.Tk()

def run_loop():
    automation.switch_to_tab(0)
    eob_data = extract_claims(pdf_path)
    print(f"Extracted {len(eob_data)} patients from PDF")
    print("Initial patient data:")
    for i, (name, dos, billed_items, total) in enumerate(eob_data):
        print(f"  Patient {i+1}: {name} - {len(billed_items)} billed items")
    
    loop_rows(automation, eob_data)
    
    # Add explicit call to print_remaining_items with debugging
    print("\n=== FINAL CHECK ===")
    print_remaining_items(eob_data)
    
    # Also print summary of what happened
    remaining_count = sum(1 for _, _, billed_items, _ in eob_data if billed_items)
    print(f"\nSummary: {remaining_count} out of {len(eob_data)} patients still have unprocessed items")


button = tk.Button(root, text="Find Starting Element", command=run_loop)
button.pack()






root.mainloop()
