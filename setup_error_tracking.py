#!/usr/bin/env python3
"""
UNIVERSAL ERROR TRACKER SETUP
=============================
Quick setup script to add error tracking to any VS Code project

Usage:
    python setup_error_tracking.py [project_name]
"""

import os
import sys
import shutil
from pathlib import Path

def setup_error_tracking(project_name=None):
    """Setup error tracking for current project"""
    
    # Get current directory and project name
    current_dir = Path.cwd()
    if not project_name:
        project_name = current_dir.name
    
    print(f"🔧 Setting up error tracking for: {project_name}")
    print(f"📁 Project directory: {current_dir}")
    
    # Create .vscode directory if it doesn't exist
    vscode_dir = current_dir / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    print(f"✅ Created .vscode directory")
    
    # Copy universal error tracker
    tracker_source = Path(__file__).parent / "universal_error_tracker.py"
    tracker_dest = current_dir / "universal_error_tracker.py"
    
    if tracker_source.exists() and not tracker_dest.exists():
        shutil.copy2(tracker_source, tracker_dest)
        print(f"✅ Copied universal_error_tracker.py")
    elif tracker_dest.exists():
        print(f"⚠️  universal_error_tracker.py already exists")
    else:
        print(f"❌ Could not find universal_error_tracker.py source")
        return False
    
    # Copy VS Code snippets
    snippets_source = Path(__file__).parent / ".vscode" / "python.code-snippets"
    snippets_dest = vscode_dir / "python.code-snippets"
    
    if snippets_source.exists():
        if snippets_dest.exists():
            # Merge with existing snippets
            print(f"⚠️  python.code-snippets already exists - manual merge required")
        else:
            shutil.copy2(snippets_source, snippets_dest)
            print(f"✅ Added VS Code snippets")
    
    # Create project-specific initialization
    init_script = current_dir / "init_error_tracking.py"
    if not init_script.exists():
        with open(init_script, 'w') as f:
            f.write(f"""# Error Tracking Initialization for {project_name}
from universal_error_tracker import initialize_tracker, print_report

def setup():
    \"\"\"Initialize error tracking for this project\"\"\"
    tracker = initialize_tracker(
        project_name="{project_name}",
        db_path="./.vscode/error_tracking.db"
    )
    
    print(f"✅ Error tracking initialized for {project_name}")
    print(f"📊 Database: {{tracker.db_path}}")
    
    # Show current status
    tracker.print_report(days=30)
    return tracker

if __name__ == "__main__":
    setup()
""")
        print(f"✅ Created init_error_tracking.py")
    
    # Add to .gitignore
    gitignore = current_dir / ".gitignore"
    gitignore_entries = [
        "# Error Tracking Database",
        ".vscode/error_tracking.db",
        "*.error_log"
    ]
    
    existing_content = ""
    if gitignore.exists():
        existing_content = gitignore.read_text()
    
    if ".vscode/error_tracking.db" not in existing_content:
        with open(gitignore, 'a') as f:
            if existing_content and not existing_content.endswith('\n'):
                f.write('\n')
            f.write('\n'.join(gitignore_entries) + '\n')
        print(f"✅ Updated .gitignore")
    
    # Create example usage file
    example_file = current_dir / "error_tracking_examples.py"
    if not example_file.exists():
        with open(example_file, 'w') as f:
            f.write(f'''"""
Error Tracking Examples for {project_name}
=========================================
"""

from universal_error_tracker import log_error, log_action, log_solution, print_report

def example_error_logging():
    """Example of logging an error with context"""
    
    # Simulate an error scenario
    try:
        # Your risky operation here
        result = 1 / 0  # This will cause a ZeroDivisionError
    except Exception as e:
        # Log the error with full context
        error_id = log_error(
            error=e,
            context_info={{
                "operation": "division",
                "numerator": 1,
                "denominator": 0
            }},
            tags=["{project_name.lower()}", "math", "division"],
            severity="ERROR"
        )
        
        # Log troubleshooting action
        action_id = log_action(
            error_id=error_id,
            action_taken="Added input validation to check for zero denominator",
            result="Input validation function created",
            success=True,
            time_spent_minutes=15,
            notes="Added validate_inputs() function to prevent division by zero"
        )
        
        # Log final solution
        solution_id = log_solution(
            error_id=error_id,
            root_cause="No input validation for division operations causing ZeroDivisionError",
            solution_description="Added comprehensive input validation before mathematical operations",
            code_changes="Added validate_inputs() function in utils.py, integrated validation in all math operations",
            prevention_measures="Create unit tests for edge cases, add automated validation checks",
            verified=True,
            effectiveness_rating=5
        )
        
        print(f"Error logged: ID {{error_id}}, Action: {{action_id}}, Solution: {{solution_id}}")

def example_manual_logging():
    """Example of manual error logging"""
    
    error_id = log_error(
        error_type="ValidationError",
        error_message="User input failed validation checks",
        file_path="validators.py",
        line_number=42,
        function_name="validate_user_input",
        context_info={{
            "input_type": "email",
            "input_value": "invalid-email",
            "validation_rule": "email_format"
        }},
        severity="WARNING",
        tags=["{project_name.lower()}", "validation", "user-input"]
    )
    
    print(f"Manual error logged: ID {{error_id}}")

def view_error_report():
    """View current error report"""
    print("📊 Current Error Report:")
    print_report(days=7)

if __name__ == "__main__":
    print("🔧 Error Tracking Examples for {project_name}")
    print("=" * 50)
    
    print("\\n1️⃣ Example Error Logging:")
    example_error_logging()
    
    print("\\n2️⃣ Manual Error Logging:")
    example_manual_logging()
    
    print("\\n3️⃣ Project Report:")
    view_error_report()
''')
        print(f"✅ Created error_tracking_examples.py")
    
    print(f"\n🎯 Setup Complete!")
    print(f"   Project: {project_name}")
    print(f"   Location: {current_dir}")
    print(f"\n📚 Next Steps:")
    print(f"   1. Run: python init_error_tracking.py")
    print(f"   2. Try: python error_tracking_examples.py")
    print(f"   3. Use VS Code snippets: 'logerror', 'logaction', 'logsolution'")
    print(f"   4. Import in your code: from universal_error_tracker import log_error")
    
    return True

def main():
    """Main entry point"""
    project_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    
    success = setup_error_tracking(project_name)
    if success:
        print(f"\n✨ Error tracking ready! Happy debugging! 🐛➡️✅")
    else:
        print(f"\n❌ Setup failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
