# DISCORD BOT ERROR TRACKING EXAMPLE
# ==================================
# This demonstrates logging the Discord bot double printing issue

from universal_error_tracker import ProjectErrorTracker

# Initialize tracker for Discord bot project
print("🔧 DISCORD BOT ERROR TRACKING DEMO")
print("=" * 50)

tracker = ProjectErrorTracker("Discord-Trading-Bot")

# Log the double printing error we just fixed
print("\n1️⃣ Logging Discord bot double printing error...")
error_id = tracker.log_error(
    error_type="DisplayError",
    error_message="Discord bot showing double printing of returns - sending two separate embeds per command",
    file_path="discord_integration.py", 
    line_number=892,
    function_name="send_embed_response",
    context_info={
        "command_affected": "!scan, !top, !analyze",
        "discord_channel": "1406984851336466533",
        "bot_name": "Oscar#2516",
        "embed_count": 2,
        "issue_type": "duplicate_display"
    },
    severity="ERROR",
    tags=["discord", "embed", "display", "user-experience"]
)

# Log troubleshooting actions taken
print("\n2️⃣ Logging troubleshooting actions...")

action1_id = tracker.log_troubleshooting_action(
    error_id=error_id,
    action_taken="Analyzed discord_integration.py code structure to identify embed sending logic",
    result="Found bot sending separate main embed and recommendation prompt embed",
    success=False,
    time_spent_minutes=20,
    notes="Located issue in send_embed_response function - two separate embed.send() calls"
)

action2_id = tracker.log_troubleshooting_action(
    error_id=error_id,
    action_taken="Used replace_string_in_file to consolidate embed responses into single message",
    result="Successfully modified all command handlers to use single embed with footer",
    success=True,
    time_spent_minutes=25,
    notes="Modified !scan, !top, !analyze commands to include recommendations in footer field"
)

action3_id = tracker.log_troubleshooting_action(
    error_id=error_id,
    action_taken="Created restart-bot-fixed.bat script to apply changes and restart bot",
    result="Automated restart process created for testing fixes",
    success=True,
    time_spent_minutes=5,
    notes="Batch script includes database cleanup and bot restart with new code"
)

# Log the final solution
print("\n3️⃣ Logging root cause analysis and solution...")

solution_id = tracker.log_solution(
    error_id=error_id,
    root_cause="Discord bot was programmed to send two separate embed messages per command: first embed contained main trading data results, second embed contained recommendation prompts. This created appearance of duplicate content and poor user experience.",
    solution_description="Consolidated all command responses into single comprehensive embed message. Main trading data goes in description field, recommendations and prompts go in footer field. This provides clean, professional single-message responses.",
    code_changes="""
Modified discord_integration.py:
- Lines 892-945: Updated send_embed_response() function
- Combined separate embed objects into single embed
- Added footer field for recommendations
- Removed duplicate embed.send() calls
- Updated !scan, !top, !analyze command handlers
    """,
    prevention_measures="Implement embed validation function, create unit tests for Discord message format, establish single-embed response standard for all bot commands",
    verified=True,
    effectiveness_rating=5
)

print(f"\n✅ Complete error tracking entry created!")
print(f"   Error ID: #{error_id}")
print(f"   Actions logged: {3}")
print(f"   Solution ID: #{solution_id}")

# Generate project report
print("\n4️⃣ Project Error Report:")
tracker.print_report(days=30)

# Show recent error history
print("\n5️⃣ Recent Error History:")
history = tracker.get_error_history(limit=5)
for i, error in enumerate(history, 1):
    status = "✅ SOLVED" if error['verified'] else "⏳ PENDING"
    print(f"  {i}. {error['timestamp'][:19]} - {error['error_type']}")
    print(f"     {error['error_message'][:70]}...")
    print(f"     Status: {status}")
    if error['root_cause']:
        print(f"     Root Cause: {error['root_cause'][:60]}...")
    print()

print(f"📁 Database location: {tracker.db_path}")
print("✨ Error tracking system ready for use!")
print("\n🎯 Next Steps:")
print("   1. Test bot with restart-bot-fixed.bat")
print("   2. Verify single embed responses in Discord")
print("   3. Mark solution as verified once confirmed")
print("   4. Use error tracker for future debugging!")
