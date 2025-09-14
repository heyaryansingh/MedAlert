#!/usr/bin/env python3
"""
MedAlert AI Chatbot Launcher
Simple script to start the backend server and open the web interface
"""

import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

def check_python_packages():
    """Check if required packages are installed"""
    required_packages = ['fastapi', 'uvicorn', 'python-multipart']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages)
    
    return True

def start_server():
    """Start the FastAPI server"""
    print("Starting MedAlert AI Chatbot Server...")
    
    # Check if chatbot_server.py exists
    if not os.path.exists('chatbot_server.py'):
        print("ERROR: chatbot_server.py not found!")
        return False
    
    # Start the server
    try:
        process = subprocess.Popen([sys.executable, 'chatbot_server.py'])
        print("Server started successfully!")
        return process
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        return None

def open_web_interface():
    """Open the web interface in the default browser"""
    print("Opening web interface...")
    
    # Check if medalert_app.html exists
    if not os.path.exists('medalert_app.html'):
        print("ERROR: medalert_app.html not found!")
        return False
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Open the HTML file
    try:
        webbrowser.open('medalert_app.html')
        print("Web interface opened in your default browser!")
        return True
    except Exception as e:
        print(f"ERROR: Failed to open web interface: {e}")
        return False

def main():
    """Main launcher function"""
    print("=" * 50)
    print("MedAlert AI Chatbot Launcher")
    print("=" * 50)
    
    # Clear previous run history by killing existing Python processes
    print("Clearing previous run history...")
    try:
        # Find and kill existing Python processes running chatbot_server.py
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        if 'python.exe' in result.stdout:
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                          capture_output=True)
            print("Previous Python processes terminated.")
        else:
            print("No previous Python processes found.")
    except Exception as e:
        print(f"Note: Could not clear previous processes: {e}")
    
    # Check and install required packages
    check_python_packages()
    
    # Start the server
    server_process = start_server()
    if not server_process:
        return
    
    # Open the web interface
    if not open_web_interface():
        server_process.terminate()
        return
    
    print("\n" + "=" * 50)
    print("MedAlert AI Chatbot System is now running!")
    print("- Backend server: http://localhost:8001")
    print("- Web interface: Opened in your default browser")
    print("=" * 50)
    
    try:
        print("\nPress Ctrl+C to stop the server and exit...")
        server_process.wait()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()
        print("Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
