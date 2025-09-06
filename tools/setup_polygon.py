"""Polygon.io MCP integration setup script.

This script helps configure the Polygon MCP server for use with FINANCIAL-TOOLS.
Run this after obtaining a Polygon.io API key.

Usage:
    python tools/setup_polygon.py --api-key YOUR_API_KEY
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install required packages for Polygon integration."""
    packages = [
        "git+https://github.com/polygon-io/mcp_polygon@v0.4.0",
        "python-dotenv"  # For environment variable management
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    return True


def create_env_file(api_key, env_path=".env"):
    """Create or update .env file with Polygon API key."""
    env_file = Path(env_path)
    
    # Read existing .env if it exists
    existing_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_vars[key] = value
    
    # Update with Polygon API key
    existing_vars['POLYGON_API_KEY'] = api_key
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.write("# FINANCIAL-TOOLS Environment Variables\n")
        for key, value in existing_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✓ Updated {env_file} with POLYGON_API_KEY")


def create_polygon_directories():
    """Create necessary directories for Polygon integration."""
    dirs = [
        "agent_trader/data_sources",
        "agent_trader/strategies/polygon",
        "knowledge_base/market_data",
        "knowledge_base/polygon_reference",
        "tests/polygon"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if "agent_trader" in dir_path or "tests" in dir_path:
            init_file = Path(dir_path) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
        print(f"✓ Created directory: {dir_path}")


def test_polygon_connection(api_key):
    """Test connection to Polygon API."""
    try:
        # Simple test using requests (should be available)
        import requests
        
        url = "https://api.polygon.io/v1/marketstatus/now"
        params = {"apikey": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Polygon API connection successful!")
            print(f"  Market status: {data.get('market', 'unknown')}")
            return True
        else:
            print(f"✗ Polygon API connection failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except ImportError:
        print("⚠ requests not available, skipping connection test")
        return True
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup Polygon.io integration")
    parser.add_argument("--api-key", required=True, help="Your Polygon.io API key")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    parser.add_argument("--skip-install", action="store_true", help="Skip package installation")
    parser.add_argument("--skip-test", action="store_true", help="Skip connection test")
    
    args = parser.parse_args()
    
    print("🚀 Setting up Polygon.io integration...")
    
    # Install dependencies
    if not args.skip_install:
        print("\n1. Installing dependencies...")
        if not install_dependencies():
            print("❌ Setup failed during dependency installation")
            sys.exit(1)
    
    # Create directories
    print("\n2. Creating project directories...")
    create_polygon_directories()
    
    # Create .env file
    print("\n3. Configuring environment...")
    create_env_file(args.api_key, args.env_file)
    
    # Test connection
    if not args.skip_test:
        print("\n4. Testing Polygon API connection...")
        if not test_polygon_connection(args.api_key):
            print("⚠ Setup completed but API connection test failed")
            print("  Please verify your API key is correct")
    
    print("\n✅ Polygon.io integration setup complete!")
    print("\nNext steps:")
    print("1. Run: python agent_trader/data_sources/polygon_client.py --test")
    print("2. Try: python tools/polygon_health_check.py")
    print("3. See POLYGON_INTEGRATION_PLAN.md for full implementation roadmap")


if __name__ == "__main__":
    main()
