# cursor.md

## Project Name
VSP Automation Agent

## Overview
This project automates insurance claim workflows for VSP using Python and Selenium. It navigates EMRs and insurance portals, extracts member info, and submits claims intelligently using a combination of rule-based logic and AI inference.

## Primary Goals
- Minimize manual data entry for staff.
- Automate member lookups using AI-generated combinations of name, DOB, and SSN.
- Validate claims before submission.
- Maintain clean, modular code that can be extended easily.

## Preferred Language
Python 3.10+

## Style Guide
- Use `snake_case` for variables and functions.
- Use `UpperCamelCase` for class names.
- Use f-strings, not `.format()` or `%` formatting.
- Prefer list comprehensions and generators over manual loops when cleaner.
- Always write docstrings for classes and public functions.

## Libraries in Use
- `selenium` for browser automation.
- `openai` for AI-assisted lookup strategy.
- `pandas` for CSV and spreadsheet manipulation.
- `re` for regex-based field parsing.

## Code Architecture
- `automation.py`: Handles low-level UI control.
- `vsp_bot.py`: Orchestrates high-level claim workflows.
- `ai_search.py`: Uses OpenAI API to infer search combos.
- `behavior.py`: (Planned) Modular agent behavior logic.
- `main.py`: Entry point for running the system.

## My Coding Preferences
- I want it **clean, modular, and hackable**.
- I prefer **explicit over clever**: if it’s readable, I can tweak it later.
- Handle edge cases gracefully — I want it to fail **loud**, not silently.
- When in doubt, log it.
- I’d rather over-document than guess later.
- Assume **Linux environment**, always.

## In-Scope Tasks for AI
- Refactor messy blocks into functions or classes.
- Suggest better error handling.
- Help write missing docstrings.
- Improve readability without breaking logic.
- Propose modular structures for future expansion.

## Out-of-Scope for AI
- Do not change file system paths without asking.
- Do not use GUI-based Selenium elements unless specified.
- Do not add packages unless there's a clear reason.
