import os
import sys
import subprocess


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if "--regtest" in sys.argv:
        subprocess.call(["coverage", "run", "-m", "pytest", "--regtest", "-rw"])
    else:
        subprocess.call(["coverage", "run", "-m", "pytest", "-m", "not regtest", "-rw"])
    print("\n\nTests completed, checking coverage...\n\n")

    subprocess.call(["coverage", "combine", "--append"])
    subprocess.call(["coverage", "report", "-m"])
    input("\n\nPress enter to quit ")


if __name__ == "__main__":
    main()
