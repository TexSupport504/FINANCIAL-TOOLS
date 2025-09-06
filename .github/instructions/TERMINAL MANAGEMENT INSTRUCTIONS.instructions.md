TERMINAL MANAGEMENT INSTRUCTIONS:

1. TERMINAL SESSION AWARENESS:

   - Always check get_terminal_output before starting new commands
   - Use existing active terminals instead of creating new ones
   - If a terminal shows an error, read the full output before proceeding
   - Don't assume terminal state - always verify current directory and environment
2. DIRECTORY NAVIGATION:

   - Always verify current working directory with pwd or Get-Location
   - Navigate to correct project directory BEFORE running application commands
   - Use absolute paths when uncertain about current location
3. ENVIRONMENT SETUP:

   - Check if virtual environment is already activated before creating new one
   - Look for existing venv activation in terminal output
   - Don't repeatedly install packages - check if already installed first
4. ERROR HANDLING:

   - Read full terminal output when commands fail
   - Don't retry the same failing command without addressing the root cause
   - If getting import errors, verify you're in correct directory with correct environment
5. COMMAND EXECUTION:

   - For Python projects: Navigate to project root, activate venv, THEN run application
   - For PowerShell: Use proper syntax and check execution policy if scripts fail
   - Don't start multiple terminals for the same task
6. TROUBLESHOOTING LOOP PREVENTION:

   - If same error occurs twice, stop and analyze the full context
   - Check file structure and dependencies before assuming command syntax issues
   - Ask user for clarification if stuck in repetitive failure pattern

EXAMPLE WORKFLOW:

1. Check terminal output: get_terminal_output
2. Verify location: Get-Location or pwd
3. Navigate if needed: cd to project directory
4. Check environment: look for (venv) prompt
5. Activate if needed: .\venv\Scripts\Activate.ps1
6. Run command: python main.py
7. If fails, read output and address specific error, don't retry blindly
