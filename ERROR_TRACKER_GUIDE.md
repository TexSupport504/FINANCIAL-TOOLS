# ERROR TRACKER INTEGRATION GUIDE
# ===============================
# How to use the Universal Error Tracker in any VS Code project

## QUICK START

### 1. Copy the error tracker to your project
```python
# Copy universal_error_tracker.py to your project root or tools folder
```

### 2. Basic Usage in any Python file
```python
from universal_error_tracker import log_error, log_action, log_solution, print_report

# Automatic error logging with exception
try:
    # Your code here
    result = risky_operation()
except Exception as e:
    error_id = log_error(
        error=e,
        context_info={"operation": "risky_operation", "params": {"x": 123}},
        tags=["database", "connection"]
    )
    
    # Log troubleshooting steps
    log_action(
        error_id=error_id,
        action_taken="Checked database connection string",
        result="Connection string is correct",
        success=False,
        time_spent_minutes=5
    )
    
    log_action(
        error_id=error_id,
        action_taken="Restarted database service",
        result="Service restarted successfully",
        success=True,
        time_spent_minutes=10
    )
    
    # Log final solution
    log_solution(
        error_id=error_id,
        root_cause="Database service was stopped due to system update",
        solution_description="Restarted the database service and added auto-start configuration",
        prevention_measures="Add health check and auto-restart script",
        verified=True,
        effectiveness_rating=5
    )

# Manual error logging
error_id = log_error(
    error_type="ValidationError", 
    error_message="User input validation failed",
    file_path="validators.py",
    line_number=45,
    function_name="validate_email",
    severity="WARNING",
    tags=["validation", "user-input"]
)

# View project report
print_report(days=30)
```

### 3. GitHub Copilot Integration

Add this to your workspace settings (.vscode/settings.json):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.analysis.extraPaths": ["./"],
    "files.associations": {
        "*.error_log": "json"
    },
    "search.exclude": {
        ".vscode/error_tracking.db": true
    }
}
```

### 4. Project-Specific Setup

Create a project initializer:
```python
# setup_error_tracking.py
from universal_error_tracker import initialize_tracker

# Initialize with project-specific settings
tracker = initialize_tracker(
    project_name="My-Awesome-Project",
    db_path="./.vscode/project_errors.db"
)

print("✅ Error tracking initialized for project")
tracker.print_report()
```

## ADVANCED FEATURES

### Custom Error Categories
```python
# E-commerce project
log_error(
    error_type="PaymentError",
    error_message="Credit card processing failed",
    tags=["payment", "stripe", "critical"],
    severity="CRITICAL",
    context_info={
        "payment_amount": 199.99,
        "card_type": "visa",
        "customer_id": "cust_123"
    }
)

# Machine Learning project  
log_error(
    error_type="ModelError",
    error_message="Training accuracy below threshold",
    tags=["ml", "training", "accuracy"],
    severity="WARNING",
    context_info={
        "accuracy": 0.82,
        "threshold": 0.85,
        "epoch": 15,
        "model_type": "CNN"
    }
)
```

### Batch Error Analysis
```python
from universal_error_tracker import ProjectErrorTracker

tracker = ProjectErrorTracker()

# Get all critical errors
critical_errors = tracker.get_error_history(limit=50, severity="CRITICAL")
print(f"Found {len(critical_errors)} critical errors")

# Get detailed analysis of specific error
error_details = tracker.get_detailed_error(error_id=5)
print("Troubleshooting timeline:")
for action in error_details['troubleshooting_actions']:
    print(f"  {action['timestamp']}: {action['action_taken']}")
```

### Integration with Existing Exception Handlers
```python
import logging
from universal_error_tracker import log_error

def setup_logging():
    logging.basicConfig(level=logging.ERROR)
    
    class ErrorTrackingHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                log_error(
                    error_type=record.exc_info[0].__name__ if record.exc_info else "LogError",
                    error_message=record.getMessage(),
                    file_path=record.pathname,
                    line_number=record.lineno,
                    function_name=record.funcName,
                    severity="CRITICAL" if record.levelno >= logging.CRITICAL else "ERROR"
                )
    
    logging.getLogger().addHandler(ErrorTrackingHandler())

# Use in your main application
setup_logging()
```

## DATABASE SCHEMA

The error tracker creates these tables in `.vscode/error_tracking.db`:

### error_log
- id (PRIMARY KEY)
- project_name
- timestamp  
- error_type
- error_message
- file_path
- line_number
- function_name
- stack_trace
- context_info (JSON)
- severity (ERROR/WARNING/CRITICAL)
- tags (comma-separated)

### troubleshooting_actions  
- id (PRIMARY KEY)
- error_id (FOREIGN KEY)
- action_timestamp
- action_taken
- result
- success (BOOLEAN)
- time_spent_minutes
- notes

### solutions
- id (PRIMARY KEY) 
- error_id (FOREIGN KEY)
- solution_timestamp
- root_cause
- solution_description
- code_changes
- prevention_measures
- verified (BOOLEAN)
- effectiveness_rating (1-5)

## BEST PRACTICES

### 1. Consistent Error Types
```python
# Good - Use consistent naming
"ConnectionError", "ValidationError", "AuthenticationError"

# Avoid - Inconsistent naming  
"connection_error", "validationFailed", "Auth Error"
```

### 2. Meaningful Context
```python
# Good - Rich context
context_info={
    "user_id": "12345",
    "action": "login", 
    "ip_address": "192.168.1.1",
    "browser": "Chrome 91.0"
}

# Avoid - Minimal context
context_info={"error": "login failed"}
```

### 3. Proper Tagging
```python
# Good - Specific, searchable tags
tags=["authentication", "oauth", "google-api", "production"]

# Avoid - Vague tags
tags=["error", "problem"]
```

### 4. Solution Documentation
```python
log_solution(
    error_id=error_id,
    root_cause="OAuth token expired due to clock skew between servers",
    solution_description="Synchronized server clocks and added token refresh logic",
    code_changes="Added token_refresh() function in auth.py lines 45-67",
    prevention_measures="Set up NTP synchronization and add token expiry monitoring",
    verified=True,
    effectiveness_rating=4
)
```

## GITHUB COPILOT PROMPTS

Use these prompts with GitHub Copilot:

```
"Add error tracking to this function using universal_error_tracker"
"Log this exception with context using error tracker" 
"Create troubleshooting steps for this error"
"Generate error report for last 7 days"
"Find similar errors in error tracking database"
```

## AUTOMATION SCRIPTS

### Daily Error Report (add to cron/Task Scheduler)
```python
# daily_error_report.py
from universal_error_tracker import print_report
import sys

if __name__ == "__main__":
    project_name = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"📊 Daily Error Report - {project_name or 'Current Project'}")
    print("=" * 60)
    print_report(days=1)
```

### Error Export for Analysis
```python
# export_errors.py  
import json
from universal_error_tracker import ProjectErrorTracker

tracker = ProjectErrorTracker()
errors = tracker.get_error_history(limit=100)

with open('error_export.json', 'w') as f:
    json.dump(errors, f, indent=2)

print("✅ Error data exported to error_export.json")
```

This system will help you maintain professional debugging practices across all your VS Code projects! 🚀
