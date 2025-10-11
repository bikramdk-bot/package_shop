import subprocess
import shutil

tools = {
    "Python": "python --version",
    "Pip": "pip --version",
    "Git": "git --version",
    "ADB": "adb version",
    "VS Code": "code --version",
    "WSL": "wsl --list --verbose"
}

def check_tool(name, cmd):
    print(f"\n🔹 Checking {name}...")
    exe = cmd.split()[0]
    if shutil.which(exe) is None:
        print(f"❌ {name} not found in PATH.")
        return

    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        print(f"✅ {name} detected:\n{output.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ {name} command error:\n{e.output.strip()}")
    except Exception as e:
        print(f"⚠️ Unexpected error while checking {name}: {e}")

print("=== 🧠 Developer Environment Check ===")

for tool, cmd in tools.items():
    check_tool(tool, cmd)

print("\n✅ Environment check completed!\n")
