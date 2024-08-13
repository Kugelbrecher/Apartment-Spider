import subprocess

scripts = [
    "./spider/list_1000m.py",
    "./spider/list_1130.py",
    "./spider/list_1140.py",
    "./spider/list_elle.py",
    "./spider/list_grandcentral.py",
    "./spider/list_linea.py",
    "./spider/list_nema.py",
]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script])
    print(f"Finished {script}")
