"""
Script to run the Django backend server
"""
import os
import sys
import subprocess

if __name__ == "__main__":
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print("=" * 60)
    print("Starting Django Backend Server")
    print("=" * 60)
    print(f"Project directory: {project_dir}")
    print("Backend API will be available at: http://localhost:8000")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
    
    # Run the Django development server
    try:
        subprocess.run([sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])
    except KeyboardInterrupt:
        print("\n\nBackend server stopped.")
