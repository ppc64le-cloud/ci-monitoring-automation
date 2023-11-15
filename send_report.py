import subprocess

def capture_output():
    result = subprocess.run(['python3', 'CI_DailyBuildUpdates.py'],capture_output=True, text=True)
    print(result.stdout)
    return result.stdout

capture_output()