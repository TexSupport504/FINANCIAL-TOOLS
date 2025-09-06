# PROJECT ERROR TRACKING & TROUBLESHOOTING LOG
# ================================================
# Universal tracking system for all VS Code projects using GitHub Copilot
# 
# Usage: Import this module in any project to log errors and solutions
# Example: from universal_error_tracker import log_error, get_error_history

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import os
import traceback
from typing import Optional, Dict, List, Any, Union

class ProjectErrorTracker:
    """
    Universal error tracking system for VS Code projects
    Automatically creates database in project root or specified location
    """
    
    def __init__(self, project_name: Optional[str] = None, db_path: Optional[str] = None):
        """
        Initialize error tracker for a project
        
        Args:
            project_name: Name of the project (auto-detected if None)
            db_path: Custom database path (defaults to project root)
        """
        self.project_name = project_name or self._detect_project_name()
        self.db_path = db_path or self._get_default_db_path()
        self._ensure_database_exists()
    
    def _detect_project_name(self) -> str:
        """Auto-detect project name from current directory or git repo"""
        cwd = Path.cwd()
        
        # Try to get from git repo name
        git_dir = cwd / '.git'
        if git_dir.exists():
            try:
                with open(git_dir / 'config', 'r') as f:
                    content = f.read()
                    if 'url = ' in content:
                        url_line = [line for line in content.split('\n') if 'url = ' in line][0]
                        repo_name = url_line.split('/')[-1].replace('.git', '').strip()
                        return repo_name
            except:
                pass
        
        # Fallback to directory name
        return cwd.name
    
    def _get_default_db_path(self) -> str:
        """Get default database path in project root"""
        return str(Path.cwd() / '.vscode' / 'error_tracking.db')
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        # Ensure .vscode directory exists
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create error_log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                file_path TEXT,
                line_number INTEGER,
                function_name TEXT,
                stack_trace TEXT,
                context_info TEXT,
                severity TEXT DEFAULT 'ERROR',
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create troubleshooting_actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS troubleshooting_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id INTEGER,
                action_timestamp TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                result TEXT,
                success BOOLEAN DEFAULT FALSE,
                time_spent_minutes INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_id) REFERENCES error_log (id)
            )
        ''')
        
        # Create solutions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id INTEGER,
                solution_timestamp TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                solution_description TEXT NOT NULL,
                code_changes TEXT,
                prevention_measures TEXT,
                verified BOOLEAN DEFAULT FALSE,
                effectiveness_rating INTEGER CHECK(effectiveness_rating BETWEEN 1 AND 5),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_id) REFERENCES error_log (id)
            )
        ''')
        
        # Create project_metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                date TEXT NOT NULL,
                total_errors INTEGER DEFAULT 0,
                errors_resolved INTEGER DEFAULT 0,
                avg_resolution_time_minutes REAL DEFAULT 0,
                most_common_error_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_error(self, 
                  error: Optional[Exception] = None,
                  error_type: Optional[str] = None,
                  error_message: Optional[str] = None,
                  file_path: Optional[str] = None,
                  line_number: Optional[int] = None,
                  function_name: Optional[str] = None,
                  context_info: Optional[Dict[str, Any]] = None,
                  severity: str = "ERROR",
                  tags: Optional[List[str]] = None) -> int:
        """
        Log an error to the tracking system
        
        Args:
            error: Exception object (if available)
            error_type: Type of error (e.g., "ValueError", "ConnectionError")
            error_message: Error description
            file_path: File where error occurred
            line_number: Line number where error occurred
            function_name: Function where error occurred
            context_info: Additional context information
            severity: ERROR, WARNING, CRITICAL
            tags: List of tags for categorization
            
        Returns:
            error_id: ID of the logged error
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract info from exception if provided
        if error:
            error_type = error_type or type(error).__name__
            error_message = error_message or str(error)
            
            # Get stack trace info
            tb = traceback.extract_tb(error.__traceback__)
            if tb:
                last_frame = tb[-1]
                file_path = file_path or last_frame.filename
                line_number = line_number or last_frame.lineno
                function_name = function_name or last_frame.name
            
            stack_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        else:
            stack_trace = None
        
        # Prepare data
        timestamp = datetime.now().isoformat()
        context_json = json.dumps(context_info) if context_info else None
        tags_str = ','.join(tags) if tags else None
        
        # Insert error
        cursor.execute('''
            INSERT INTO error_log 
            (project_name, timestamp, error_type, error_message, file_path, line_number, 
             function_name, stack_trace, context_info, severity, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.project_name, timestamp, error_type, error_message, file_path, 
              line_number, function_name, stack_trace, context_json, severity, tags_str))
        
        error_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"🚨 Error logged: ID #{error_id} - {error_type}: {error_message}")
        return error_id
    
    def log_troubleshooting_action(self, 
                                   error_id: int,
                                   action_taken: str,
                                   result: Optional[str] = None,
                                   success: bool = False,
                                   time_spent_minutes: Optional[int] = None,
                                   notes: Optional[str] = None) -> int:
        """
        Log a troubleshooting action taken for an error
        
        Args:
            error_id: ID of the error being troubleshooted
            action_taken: Description of the action taken
            result: Result of the action
            success: Whether the action was successful
            time_spent_minutes: Time spent on this action
            notes: Additional notes
            
        Returns:
            action_id: ID of the logged action
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO troubleshooting_actions 
            (error_id, action_timestamp, action_taken, result, success, time_spent_minutes, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (error_id, timestamp, action_taken, result, success, time_spent_minutes, notes))
        
        action_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        status = "✅ SUCCESS" if success else "⏳ IN PROGRESS"
        print(f"🔧 Action logged: ID #{action_id} - {status}")
        return action_id
    
    def log_solution(self,
                     error_id: int,
                     root_cause: str,
                     solution_description: str,
                     code_changes: Optional[str] = None,
                     prevention_measures: Optional[str] = None,
                     verified: bool = False,
                     effectiveness_rating: Optional[int] = None) -> int:
        """
        Log the final solution and root cause analysis
        
        Args:
            error_id: ID of the error being solved
            root_cause: Root cause analysis summary
            solution_description: Description of the solution
            code_changes: Code changes made (if any)
            prevention_measures: Measures to prevent recurrence
            verified: Whether the solution has been verified to work
            effectiveness_rating: 1-5 rating of solution effectiveness
            
        Returns:
            solution_id: ID of the logged solution
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO solutions 
            (error_id, solution_timestamp, root_cause, solution_description, 
             code_changes, prevention_measures, verified, effectiveness_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (error_id, timestamp, root_cause, solution_description, 
              code_changes, prevention_measures, verified, effectiveness_rating))
        
        solution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Solution logged: ID #{solution_id} - Root cause: {root_cause[:50]}...")
        return solution_id
    
    def get_error_history(self, limit: int = 10, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent error history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT e.id, e.timestamp, e.error_type, e.error_message, e.severity,
                   s.root_cause, s.solution_description, s.verified
            FROM error_log e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE e.project_name = ?
        '''
        params = [self.project_name]
        
        if severity:
            query += ' AND e.severity = ?'
            params.append(severity)
        
        query += ' ORDER BY e.timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'timestamp': row[1],
                'error_type': row[2],
                'error_message': row[3],
                'severity': row[4],
                'root_cause': row[5],
                'solution_description': row[6],
                'verified': bool(row[7]) if row[7] is not None else False
            }
            for row in results
        ]
    
    def get_detailed_error(self, error_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific error"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get error details
        cursor.execute('''
            SELECT * FROM error_log WHERE id = ?
        ''', (error_id,))
        error_row = cursor.fetchone()
        
        if not error_row:
            return {"error": "Error not found"}
        
        # Get troubleshooting actions
        cursor.execute('''
            SELECT * FROM troubleshooting_actions WHERE error_id = ? ORDER BY action_timestamp
        ''', (error_id,))
        actions = cursor.fetchall()
        
        # Get solution
        cursor.execute('''
            SELECT * FROM solutions WHERE error_id = ?
        ''', (error_id,))
        solution_row = cursor.fetchone()
        
        conn.close()
        
        return {
            'error_details': {
                'id': error_row[0],
                'project_name': error_row[1],
                'timestamp': error_row[2],
                'error_type': error_row[3],
                'error_message': error_row[4],
                'file_path': error_row[5],
                'line_number': error_row[6],
                'function_name': error_row[7],
                'stack_trace': error_row[8],
                'context_info': json.loads(error_row[9]) if error_row[9] else None,
                'severity': error_row[10],
                'tags': error_row[11].split(',') if error_row[11] else []
            },
            'troubleshooting_actions': [
                {
                    'id': action[0],
                    'timestamp': action[2],
                    'action_taken': action[3],
                    'result': action[4],
                    'success': bool(action[5]),
                    'time_spent_minutes': action[6],
                    'notes': action[7]
                }
                for action in actions
            ],
            'solution': {
                'id': solution_row[0] if solution_row else None,
                'timestamp': solution_row[2] if solution_row else None,
                'root_cause': solution_row[3] if solution_row else None,
                'solution_description': solution_row[4] if solution_row else None,
                'code_changes': solution_row[5] if solution_row else None,
                'prevention_measures': solution_row[6] if solution_row else None,
                'verified': bool(solution_row[7]) if solution_row else False,
                'effectiveness_rating': solution_row[8] if solution_row else None
            } if solution_row else None
        }
    
    def generate_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate project error report for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Total errors in period
        cursor.execute('''
            SELECT COUNT(*) FROM error_log 
            WHERE project_name = ? AND timestamp >= ?
        ''', (self.project_name, start_date.isoformat()))
        total_errors = cursor.fetchone()[0]
        
        # Errors by severity
        cursor.execute('''
            SELECT severity, COUNT(*) FROM error_log 
            WHERE project_name = ? AND timestamp >= ?
            GROUP BY severity
        ''', (self.project_name, start_date.isoformat()))
        errors_by_severity = dict(cursor.fetchall())
        
        # Most common error types
        cursor.execute('''
            SELECT error_type, COUNT(*) FROM error_log 
            WHERE project_name = ? AND timestamp >= ?
            GROUP BY error_type ORDER BY COUNT(*) DESC LIMIT 5
        ''', (self.project_name, start_date.isoformat()))
        common_errors = cursor.fetchall()
        
        # Resolution rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END) as resolved
            FROM error_log e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE e.project_name = ? AND e.timestamp >= ?
        ''', (self.project_name, start_date.isoformat()))
        result = cursor.fetchone()
        total, resolved = result if result else (0, 0)
        resolution_rate = (resolved / total * 100) if total > 0 else 0
        
        # Average resolution time
        cursor.execute('''
            SELECT AVG(
                CASE 
                    WHEN s.solution_timestamp IS NOT NULL 
                    THEN (julianday(s.solution_timestamp) - julianday(e.timestamp)) * 24 * 60 
                    ELSE NULL 
                END
            ) as avg_minutes
            FROM error_log e
            LEFT JOIN solutions s ON e.id = s.error_id
            WHERE e.project_name = ? AND e.timestamp >= ? AND s.id IS NOT NULL
        ''', (self.project_name, start_date.isoformat()))
        avg_resolution_minutes = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'project_name': self.project_name,
            'report_period': f'{days} days',
            'total_errors': total_errors,
            'errors_by_severity': errors_by_severity,
            'most_common_errors': common_errors,
            'resolution_rate': f"{resolution_rate:.1f}%",
            'avg_resolution_time_minutes': round(avg_resolution_minutes, 1),
            'generated_at': datetime.now().isoformat()
        }
    
    def print_report(self, days: int = 7):
        """Print a formatted report to console"""
        report = self.generate_report(days)
        
        print(f"\n📊 ERROR TRACKING REPORT - {report['project_name']}")
        print("=" * 60)
        print(f"📅 Period: Last {report['report_period']}")
        print(f"🚨 Total Errors: {report['total_errors']}")
        print(f"✅ Resolution Rate: {report['resolution_rate']}")
        print(f"⏱️  Average Resolution Time: {report['avg_resolution_time_minutes']} minutes")
        
        print("\n🔥 Errors by Severity:")
        for severity, count in report['errors_by_severity'].items():
            print(f"  {severity}: {count}")
        
        print("\n🎯 Most Common Error Types:")
        for error_type, count in report['most_common_errors']:
            print(f"  {error_type}: {count} occurrences")
        
        print(f"\n📈 Report generated: {report['generated_at'][:19]}")

# Global instance for easy access
_tracker = None

def initialize_tracker(project_name: Optional[str] = None, db_path: Optional[str] = None):
    """Initialize global error tracker"""
    global _tracker
    _tracker = ProjectErrorTracker(project_name, db_path)
    return _tracker

def log_error(*args, **kwargs) -> int:
    """Log error using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.log_error(*args, **kwargs)

def log_action(*args, **kwargs) -> int:
    """Log troubleshooting action using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.log_troubleshooting_action(*args, **kwargs)

def log_solution(*args, **kwargs) -> int:
    """Log solution using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.log_solution(*args, **kwargs)

def get_history(*args, **kwargs) -> List[Dict[str, Any]]:
    """Get error history using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.get_error_history(*args, **kwargs)

def get_error_details(error_id: int) -> Dict[str, Any]:
    """Get detailed error information using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.get_detailed_error(error_id)

def generate_report(*args, **kwargs) -> Dict[str, Any]:
    """Generate report using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.generate_report(*args, **kwargs)

def print_report(*args, **kwargs):
    """Print formatted report using global tracker"""
    if not _tracker:
        initialize_tracker()
    return _tracker.print_report(*args, **kwargs)

# Usage example and testing
if __name__ == "__main__":
    print("🔧 UNIVERSAL ERROR TRACKER - Demo Mode")
    print("=====================================")
    
    # Example usage
    tracker = ProjectErrorTracker("Discord-Trading-Bot")
    
    # Log an error
    print("\n1️⃣ Logging sample error...")
    error_id = tracker.log_error(
        error_type="ConnectionError",
        error_message="Failed to connect to Discord API - double printing returns",
        file_path="discord_integration.py",
        line_number=150,
        function_name="send_embed_response",
        context_info={
            "token": "present", 
            "channel_id": "1406984851336466533",
            "command": "!scan",
            "user_id": "123456789"
        },
        severity="ERROR",
        tags=["discord", "api", "double-printing", "embed"]
    )
    
    # Log troubleshooting actions
    print("\n2️⃣ Logging troubleshooting actions...")
    tracker.log_troubleshooting_action(
        error_id=error_id,
        action_taken="Checked Discord bot embed structure in send_embed_response function",
        result="Found bot sending two separate embeds - main results and recommendation prompt",
        success=False,
        time_spent_minutes=15,
        notes="Identified root cause: separate embed calls causing double display"
    )
    
    tracker.log_troubleshooting_action(
        error_id=error_id,
        action_taken="Modified discord_integration.py to combine embeds into single response",
        result="Successfully merged main content and recommendation into single embed with footer",
        success=True,
        time_spent_minutes=20,
        notes="Applied replace_string_in_file operations to consolidate embed responses"
    )
    
    # Log final solution
    print("\n3️⃣ Logging final solution...")
    tracker.log_solution(
        error_id=error_id,
        root_cause="Discord bot was sending two separate embed messages per command: main results embed followed by recommendation prompt embed, causing appearance of duplicate content",
        solution_description="Consolidated all command responses into single embed with main content in description and recommendations in footer field",
        code_changes="Modified send_embed_response() function to use single embed with footer instead of separate embeds. Updated !scan, !top, !analyze commands to use unified embed structure.",
        prevention_measures="Implement embed validation function, add unit tests for Discord response format, create embed template system",
        verified=True,
        effectiveness_rating=5
    )
    
    print("\n4️⃣ Generating report...")
    tracker.print_report(days=30)
    
    print("\n5️⃣ Recent Error History:")
    history = tracker.get_error_history()
    for i, error in enumerate(history, 1):
        status = "✅ SOLVED" if error['verified'] else "⏳ PENDING"
        print(f"  {i}. {error['timestamp'][:19]} - {error['error_type']}: {error['error_message'][:60]}... [{status}]")
    
    print(f"\n📁 Database created at: {tracker.db_path}")
    print("✨ Error tracking system ready for use across all VS Code projects!")
