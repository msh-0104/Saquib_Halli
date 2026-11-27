import os
import sys
import shutil
import subprocess
import zipfile

def run_step(name, command):
    print(f"\n[BUILD] Step: {name}...")
    
    # Handle list or string commands safely without path-space breaking
    if isinstance(command, list):
        result = subprocess.run(command)
    else:
        result = subprocess.run(command, shell=True)
        
    if result.returncode != 0:
        print(f"[ERROR] Build failed during: {name}")
        sys.exit(1)
    print(f"[SUCCESS] {name} completed.")

def main():
    print("=========================================")
    print(" Starting Brownfield Todo App Build Process")
    print("=========================================")

    # 1. Ensure artifacts directory exists
    os.makedirs("artifacts", exist_ok=True)

    # 2. Clean old build artifacts / reports if needed
    for filename in ["server.log", "server.err.log"]:
        path = os.path.join("artifacts", filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    print("[SUCCESS] Cleaned old build logs.")

    # 3. Database Schema Initialization
    run_step(
        "Database Schema Initialization",
        [sys.executable, "-c", "from src.database import Database, DatabaseConfig; db = Database(DatabaseConfig(path='todo.db')); db.init_schema()"]
    )

    # 4. Run Pytest Suite and generate consolidated HTML report in artifacts/
    run_step(
        "Automated Test Suite Execution",
        [sys.executable, "-m", "pytest", "tests/", "--html=artifacts/report.html", "--self-contained-html"]
    )

    # 5. Package Clean Deployable Artifact (Excluding .venv, .git, cache)
    print("\n[BUILD] Step: Packaging Deployable Artifact...")
    artifact_zip_path = os.path.join("artifacts", "todo_app_bundle.zip")
    
    # Essential items to include in the deployment bundle
    include_items = ["src", "tests", "server.py", "service.py", "build.py", "pyproject.toml", "README.md", "todo.db"]
    
    with zipfile.ZipFile(artifact_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in include_items:
            if os.path.isfile(item):
                zipf.write(item)
                print(f"  Added file: {item}")
            elif os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    # Skip cache and virtual environment folders
                    dirs[:] = [d for d in dirs if d not in ['.pytest_cache', '__pycache__', '.venv', '.git']]
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path)
                        print(f"  Added: {file_path}")
                        
    print(f"[SUCCESS] Deployable artifact created at: {artifact_zip_path}")

    print("\n=========================================")
    print(" Build & Packaging Completed Successfully!")
    print("=========================================")

if __name__ == "__main__":
    main()
