import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from threading import Thread
import ast
import textwrap
import queue
import logging
from logging.handlers import QueueHandler

# set env file to /home/jake/Code/.env
load_dotenv("/home/jake/Code/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from rich.console import Console
from rich.syntax import Syntax
from rich.logging import RichHandler

# Create a queue for thread-safe logging
log_queue = queue.Queue()

def strip_rich_formatting(text):
    """Remove rich text formatting from a string."""
    # Remove color codes
    text = re.sub(r'\[(?:bold )?(?:red|green|yellow|blue|magenta|cyan|white|black)\]', '', text)
    text = re.sub(r'\[/(?:bold )?(?:red|green|yellow|blue|magenta|cyan|white|black)\]', '', text)
    # Remove bold markers
    text = re.sub(r'\[bold\]', '', text)
    text = re.sub(r'\[/bold\]', '', text)
    # Remove any remaining rich text markers
    text = re.sub(r'\[.*?\]', '', text)
    return text

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            # Format the record
            msg = self.format(record)
            # Strip rich formatting
            msg = strip_rich_formatting(msg)
            # Put the formatted message in the queue
            log_queue.put(msg)
        except Exception:
            self.handleError(record)

# Set up logging
console = Console()

# Create handlers
rich_handler = RichHandler(rich_tracebacks=True)
queue_handler = QueueHandler()
queue_handler.setFormatter(logging.Formatter("%(message)s"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[rich_handler, queue_handler]
)

def get_completion(prompt: str, model="gpt-4", temperature=0.3):
    system_message = """You are a code generator. Follow these rules strictly:
1. Return ONLY the function code, nothing else
2. Do not include any explanations, examples, or markdown formatting
3. Do not include any human-readable text or comments
4. Do not include any example usage or test cases
5. The response should be a single, clean Python function
6. Do not wrap the code in markdown code blocks
7. Do not add any introductory or concluding text
8. If the prompt asks for a class method, include only the method definition
9. If the prompt asks for a standalone function, include only the function definition
10. You will see a list of examples of how the code is written. Use it as a good clue as to how to write the code"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def extract_all_code_blocks(response: str) -> str:
    # Remove any markdown code block markers
    code = re.sub(r'```(?:python)?\n?', '', response)
    code = re.sub(r'```$', '', code)
    
    # Remove any explanatory text
    code = re.sub(r'^Here is.*?:\n', '', code, flags=re.DOTALL)
    code = re.sub(r'You can.*?$', '', code, flags=re.DOTALL)
    
    # Remove any example usage
    code = re.sub(r'For example.*?$', '', code, flags=re.DOTALL)
    
    # Remove any remaining markdown formatting
    code = re.sub(r'`.*?`', '', code)
    
    # Clean up whitespace
    code = code.strip()
    
    # If we have multiple functions, take the first one
    if 'def ' in code:
        # Find the first function definition
        first_def = code.find('def ')
        # Find the next function definition or end of string
        next_def = code.find('\ndef ', first_def + 1)
        if next_def == -1:
            code = code[first_def:]
        else:
            code = code[first_def:next_def]
    
    return code


def extract_class_names(filepath: Path):
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    except Exception as e:
        console.print(f"[red]Failed to parse classes from file: {e}[/red]")
        return []


def extract_method_names_by_class(filepath: Path, class_name: str):
    if not filepath.exists() or not class_name:
        return []
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return [
                    n.name for n in node.body
                    if isinstance(n, ast.FunctionDef) and n.name != "__init__"
                ]
        return []
    except Exception as e:
        console.print(f"[red]Failed to parse methods from class {class_name}: {e}[/red]")
        return []



def insert_or_replace_in_class(filepath: Path, class_name: str, method_name: str, content: str, prompt: str):
    try:
        logging.info(f"Processing file: {filepath}")
        logging.info(f"Class: {class_name}, Method: {method_name or 'New Method'}")
        
        with open(filepath, "r") as f:
            lines = f.readlines()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            "\n" + "#" * 80 + "\n"
            f"# Generated by CodeClerk\n"
            f"# Prompt: {prompt}\n"
            f"# Timestamp: {timestamp}\n"
            + "#" * 80 + "\n"
        )

        new_lines = []
        inside_class = False
        inside_target_method = False
        indent = "    "
        replaced = False
        cleaned_content = None
        function_name = "Unknown"
        line_count = 0
        class_found = False
        injection_start_line = 0
        current_line = 0

        # Calculate header line count (including newlines)
        header_line_count = len(header.splitlines())
        # Account for the extra newlines we add (2 at the end)
        extra_newlines = 2

        # Extract function name from content
        for line in content.split('\n'):
            if line.strip().startswith('def '):
                function_name = line.strip().split('def ')[1].split('(')[0]
                break

        for i, line in enumerate(lines):
            current_line += 1
            if re.match(rf"^class {class_name}\b", line):
                inside_class = True
                class_found = True
                new_lines.append(line)
                continue
            if inside_class:
                if re.match(r"^\S", line):  # dedent = class ends
                    if not replaced and method_name:
                        new_lines.append(f"{indent}# insert failed, method not found\n")
                    if not method_name:
                        cleaned_content = textwrap.dedent(content).strip()
                        indented_content = "\n".join(indent + line for line in cleaned_content.splitlines())
                        injection_start_line = current_line + 1  # +1 for the newline
                        new_lines.append("\n" + indent + header.replace("\n", f"\n{indent}") + "\n" + indented_content + "\n\n")
                        line_count = len(cleaned_content.splitlines()) + header_line_count + extra_newlines
                    inside_class = False
                if method_name:
                    if re.match(rf"^\s+def {method_name}\(", line):
                        inside_target_method = True
                        replaced = True
                        cleaned_content = textwrap.dedent(content).strip()
                        indented_content = "\n".join(indent + line for line in cleaned_content.splitlines())
                        injection_start_line = current_line
                        new_lines.append("\n" + indent + header.replace("\n", f"\n{indent}") + "\n" + indented_content + "\n\n")
                        line_count = len(cleaned_content.splitlines()) + header_line_count + extra_newlines
                        continue
                    if inside_target_method and re.match(r"^\s+def ", line):
                        inside_target_method = False
                if not inside_target_method:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # If we're at the end of the file and still inside the class, add the content
        if inside_class and not replaced and not method_name:
            cleaned_content = textwrap.dedent(content).strip()
            indented_content = "\n".join(indent + line for line in cleaned_content.splitlines())
            injection_start_line = current_line + 1  # +1 for the newline
            new_lines.append("\n" + indent + header.replace("\n", f"\n{indent}") + "\n" + indented_content + "\n\n")
            line_count = len(cleaned_content.splitlines()) + header_line_count + extra_newlines

        if not class_found:
            logging.error(f"Class '{class_name}' not found in file")
            return

        if cleaned_content is None:
            logging.warning("Warning: No content was processed")
            return

        with open(filepath, "w") as f:
            f.writelines(new_lines)

        injection_end_line = injection_start_line + line_count - 1
        logging.info(f"✅ {'Replaced' if method_name else 'Inserted'} into class '{class_name}' in {filepath}")
        logging.info(f"📝 Function: {function_name} | Lines: {injection_start_line}-{injection_end_line}")
        
        # Force reload the file
        if filepath.exists():
            with open(filepath, "r") as f:
                f.read()
    except Exception as e:
        logging.error(f"Failed to inject code: {str(e)}")
        logging.error(f"Error occurred while processing class '{class_name}'")
        logging.error(f"Method: {method_name or 'New Method'}")
        logging.error(f"File: {filepath}")

def write_to_file(filepath: Path, content: str, append: bool, prompt: str):
    try:
        logging.info(f"Processing file: {filepath}")
        logging.info(f"Mode: {'Append' if append else 'Write'}")
        
        mode = "a" if append else "w"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            "\n" + "#" * 80 + "\n"
            f"# Generated by CodeClerk\n"
            f"# Prompt: {prompt}\n"
            f"# Timestamp: {timestamp}\n"
            + "#" * 80 + "\n"
        )
        cleaned = extract_all_code_blocks(content)
        if not cleaned:
            logging.warning("Warning: No code blocks found in content")
            return
            
        cleaned_content = textwrap.dedent(cleaned).strip()
        if not cleaned_content:
            logging.warning("Warning: Content is empty after cleaning")
            return
        
        # Extract function name and count lines
        function_name = "Unknown"
        line_count = 0
        for line in cleaned_content.split('\n'):
            if line.strip().startswith('def '):
                function_name = line.strip().split('def ')[1].split('(')[0]
            if line.strip() and not line.strip().startswith('#'):
                line_count += 1
        
        with open(filepath, mode) as f:
            f.write(header + cleaned_content + "\n")
        
        logging.info(f"✅ Code {'appended to' if append else 'written to'} {filepath}")
        logging.info(f"📝 Function: {function_name} | Lines: {line_count}")
        
        # Force reload the file
        if filepath.exists():
            with open(filepath, "r") as f:
                f.read()
    except Exception as e:
        logging.error(f"Failed to write code: {str(e)}")
        logging.error(f"Error occurred while writing to {filepath}")
        logging.error(f"Mode: {'Append' if append else 'Write'}")

def process_log_queue(log_text):
    """Process log messages from the queue and update the text widget."""
    try:
        while True:
            msg = log_queue.get_nowait()
            log_text.configure(state='normal')
            log_text.insert(tk.END, msg + '\n')
            log_text.see(tk.END)
            log_text.configure(state='disabled')
    except queue.Empty:
        pass
    finally:
        # Schedule the next check
        log_text.after(100, lambda: process_log_queue(log_text))

def read_html_state() -> str:
    """Read and clean the HTML state file if it exists."""
    try:
        state_path = Path('config/debug/state.html')
        if not state_path.exists():
            return ""
        
        with open(state_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Clean up the HTML for better readability
        # Remove excessive whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        # Remove comments
        html_content = re.sub(r'<!--.*?-->', '', html_content)
        # Remove script and style tags
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        
        return html_content.strip()
    except Exception as e:
        logging.error(f"Failed to read HTML state: {str(e)}")
        return ""

def read_destination_file(filepath: Path, max_lines: int = 100) -> str:
    """Read the first N lines of the destination file for context."""
    try:
        if not filepath.exists():
            return ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            
            content = ''.join(lines)
            if i >= max_lines:
                content += f"\n# ... (showing first {max_lines} lines)\n"
            return content.strip()
    except Exception as e:
        logging.error(f"Failed to read destination file: {str(e)}")
        return ""

def run_gui():
    def update_class_dropdown():
        filepath = Path(filepath_entry.get().strip())
        class_dropdown['values'] = extract_class_names(filepath)
        class_dropdown.set('')
        method_dropdown.set('')
        method_dropdown['values'] = []

    def on_class_select(event):
        filepath = Path(filepath_entry.get().strip())
        selected_class = class_dropdown.get()
        method_dropdown['values'] = extract_method_names_by_class(filepath, selected_class)
        method_dropdown.set('')

    def on_submit():
        prompt = prompt_entry.get("1.0", "end-1c").strip()
        html_context = html_entry.get("1.0", "end-1c").strip()
        filepath_input = filepath_entry.get().strip()

        if not prompt:
            logging.warning("Please enter a prompt.")
            return

        filepath = Path(filepath_input) if filepath_input else Path(__file__).parent / "ai_written_functions.py"
        append = filepath.exists()
        selected_class = class_dropdown.get().strip()
        selected_method = method_dropdown.get().strip()

        def worker():
            logging.info("Generating code...")
            try:
                # Build the prompt with context
                prompt_parts = []
                
                # Add the original prompt (main instruction)
                prompt_parts.append(prompt)
                
                # Add the rules about only returning code
                prompt_parts.append("\n\nIMPORTANT: Return ONLY the function code, nothing else. Do not include any explanations, examples, or markdown formatting. Do not include any human-readable text or comments. The response should be a single, clean Python function.")
                
                # Add HTML context if provided
                if html_context:
                    prompt_parts.append(f"\n\nHere is the HTML that is surrounding the locator we're trying to interact with:\n{html_context}")
                    logging.info("Including HTML context in prompt")
                
                # Add code structure examples if destination file exists
                if filepath.exists():
                    file_context = read_destination_file(filepath, max_lines=300)
                    if file_context:
                        prompt_parts.append(f"\n\nPlease use the following provided examples of the class and method structures to make your methods compliant with the code's structure:\n```python\n{file_context}\n```")
                        logging.info("Including code structure examples in prompt")
                
                # Combine all parts
                final_prompt = "\n".join(prompt_parts)
                
                code_raw = get_completion(final_prompt)
                logging.info("\nRaw AI Response:")
                logging.info("```python")
                logging.info(code_raw)
                logging.info("```\n")
                
                code = extract_all_code_blocks(code_raw)
                if selected_class:
                    insert_or_replace_in_class(filepath, selected_class, selected_method if selected_method else None, code, prompt)
                else:
                    write_to_file(filepath, code, append, prompt)
                logging.info(f"✅ Successfully completed operation")
                update_class_dropdown()
            except Exception as e:
                logging.error(f"Error: {str(e)}")

        Thread(target=worker).start()

    def choose_file():
        filepath = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if filepath:
            filepath_entry.delete(0, tk.END)
            filepath_entry.insert(0, filepath)
            update_class_dropdown()

    root = tk.Tk()
    root.title("CodeClerk GUI")
    root.geometry("800x700")  # Made window larger to accommodate HTML field

    # Create main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Top section for inputs
    input_frame = tk.Frame(main_frame)
    input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # Main prompt section
    tk.Label(input_frame, text="Enter your prompt:", font=("Arial", 12)).pack(pady=(0, 5))
    prompt_entry = tk.Text(input_frame, font=("Consolas", 11), height=4)
    prompt_entry.pack(fill=tk.X, pady=(0, 10))

    # HTML context section
    tk.Label(input_frame, text="HTML Context (optional):", font=("Arial", 12)).pack(pady=(0, 5))
    html_entry = tk.Text(input_frame, font=("Consolas", 11), height=3)
    html_entry.pack(fill=tk.X, pady=(0, 10))

    path_frame = tk.Frame(input_frame)
    path_frame.pack(fill=tk.X, pady=5)
    tk.Label(path_frame, text="Destination File:", font=("Arial", 10)).pack(side="left")
    filepath_entry = tk.Entry(path_frame, font=("Consolas", 10), width=50)
    filepath_entry.insert(0, str(Path.cwd() / "ai_written_functions.py"))
    filepath_entry.pack(side="left", padx=5, fill=tk.X, expand=True)
    tk.Button(path_frame, text="Browse", command=choose_file).pack(side="right")

    class_frame = tk.Frame(input_frame)
    class_frame.pack(fill=tk.X, pady=5)
    tk.Label(class_frame, text="Detected Classes:", font=("Arial", 10)).pack(side="left")
    class_dropdown = ttk.Combobox(class_frame, font=("Consolas", 10), state="readonly")
    class_dropdown.pack(side="left", padx=5, fill=tk.X, expand=True)
    class_dropdown.bind("<<ComboboxSelected>>", on_class_select)

    method_frame = tk.Frame(input_frame)
    method_frame.pack(fill=tk.X, pady=5)
    tk.Label(method_frame, text="Methods in Class:", font=("Arial", 10)).pack(side="left")
    method_dropdown = ttk.Combobox(method_frame, font=("Consolas", 10), state="readonly")
    method_dropdown.pack(side="left", padx=5, fill=tk.X, expand=True)

    # Single generate button
    submit_button = tk.Button(
        input_frame, 
        text="Generate Code", 
        command=on_submit, 
        font=("Arial", 12), 
        bg="#4CAF50", 
        fg="white"
    )
    submit_button.pack(fill=tk.X, pady=10)

    # Log section
    log_frame = tk.LabelFrame(main_frame, text="Log Output", font=("Arial", 10))
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 10), height=10)
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    log_text.configure(state='disabled')

    # Start processing the log queue
    process_log_queue(log_text)

    update_class_dropdown()
    root.mainloop()


if __name__ == "__main__":
    run_gui()