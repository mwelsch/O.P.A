import os
import sys
import shutil
import subprocess

SRC_DIR = "/src"
OUTPUT_DIR = "/output"

CLIENT_FILE = os.path.join(SRC_DIR, "client.py")
REQUIREMENTS_FILE = os.path.join(SRC_DIR, "requirements.txt")

def install_runtime_deps():
    if os.path.exists(REQUIREMENTS_FILE):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE], check=True)

def build_linux():
    print("Building Linux executable...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "client",
        "--distpath", OUTPUT_DIR,
        "--workpath", "/tmp/pyinstaller",
        "--specpath", "/tmp/pyinstaller",
        "--console",
        CLIENT_FILE
    ], check=True)
    
    shutil.move(os.path.join(OUTPUT_DIR, "client"), os.path.join(OUTPUT_DIR, "client-linux"))
    print(f"Linux executable: {OUTPUT_DIR}/client-linux")

def build_windows():
    print("Building Windows executable...")
    
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "client",
        "--distpath", OUTPUT_DIR,
        "--workpath", "/tmp/pyinstaller",
        "--specpath", "/tmp/pyinstaller",
        "--console",
        "--target-arch", "win64",
        CLIENT_FILE
    ], check=True)
    
    shutil.move(os.path.join(OUTPUT_DIR, "client.exe"), os.path.join(OUTPUT_DIR, "client.exe"))
    print(f"Windows executable: {OUTPUT_DIR}/client.exe")

def main():
    if os.name == 'nt':
        build_windows()
    else:
        build_linux()

if __name__ == "__main__":
    install_runtime_deps()
    main()
