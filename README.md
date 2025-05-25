# Agent - Automated Healthcare Data Management

A Python-based automation framework for managing healthcare data across multiple systems, with a focus on patient information and insurance processing.

## Project Structure

```
Agent/
├── actions/          # Action definitions and handlers
├── config/          # Configuration files and system-specific mappings
│   └── rev_map/     # RevolutionEHR specific page mappings
├── core/            # Core functionality and base classes
├── logs/            # Application logs
├── tests/           # Test suite
└── main.py          # Application entry point
```

## Core Components

### Base Classes (`core/base.py`)

The foundation of the application, providing essential classes for data management:

- `Patient`: Data class for storing patient information
- `PatientContext`: Manages patient session state and cookies
- `BasePage`: Base class for all page handlers
- `PatientManager`: Thread-safe patient data management

### Page Handlers (`config/rev_map/`)

System-specific implementations for interacting with different pages:

- `PatientPage`: Handles patient search and navigation
- `InsuranceTab`: Manages insurance information
- `InvoicePage`: Handles invoice-related operations
- `ClaimsPage`: Manages claims processing

### Workflows (`core/workflow.py`)

Orchestrates complex operations across multiple pages:

- `PatientWorkflow`: Coordinates patient-related operations
  - Insurance data collection
  - Patient information updates
  - Cross-system data synchronization

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run tests to verify setup:
```bash
pytest tests/
```

## Usage

### Basic Patient Workflow

```python
from core.base import Patient, PatientManager
from core.workflow import PatientWorkflow
from core.playwright_handler import get_handler

# Initialize components
handler = get_handler()
manager = PatientManager()

# Create or load patient
patient = Patient(
    first_name="John",
    last_name="Doe",
    date_of_birth=datetime(1990, 1, 1)
)

# Run workflow
workflow = PatientWorkflow(handler, patient, manager)
workflow.run_insurance_workflow()
```

### Custom Page Handlers

All page handlers inherit from `BasePage` and can be extended:

```python
from core.base import BasePage, PatientContext

class CustomPage(BasePage):
    def _validate_patient_required(self):
        if not self.context or not self.context.patient:
            raise ValueError("CustomPage requires a patient context")
    
    def custom_operation(self):
        # Your implementation here
        pass
```

## Development Guidelines

### Adding New Features

1. Create appropriate page handlers in `config/rev_map/`
2. Extend `PatientWorkflow` for new workflows
3. Add tests in `tests/`
4. Update documentation

### Best Practices

- Always use the `PatientManager` for patient data access
- Implement proper error handling in page handlers
- Use the `PatientContext` for session management
- Write tests for new functionality
- Document new features in this README

## Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_patient_workflow.py
```

## Error Handling

The framework includes comprehensive error handling:

- Page handlers include try-catch blocks
- Screenshots are taken on failures
- Detailed logging is implemented
- Session state is preserved

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## License

[Your License Here]

## Support

[Your Support Information Here] 