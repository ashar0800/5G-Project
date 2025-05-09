# orchestrator.py
import subprocess
import time
import os
import sys
import signal
import psutil

# Define scripts and their dependencies
scripts = [
    {"name": "producer", "command": ["python", "producer.py"], "dependencies": [], "delay_start": 0},
    {"name": "processor", "command": ["python", "processor.py"], "dependencies": ["producer"], "delay_start": 3},
    {"name": "trainer", "command": ["python", "trainer.py"], "dependencies": ["processor"], "delay_start": 3},
    {"name": "deployer", "command": ["python", "deployer.py"], "dependencies": ["trainer", "processor"], "delay_start": 3},
    {
        "name": "drift_detector",
        "command": ["python", "drift_detector.py"],
        "dependencies": ["deployer", "processor"],
        "delay_start": 3,
    },
    {"name": "alerter", "command": ["python", "alerter.py"], "dependencies": ["drift_detector"], "delay_start": 3},
    {"name": "allocator", "command": ["python", "allocator.py"], "dependencies": ["deployer"], "delay_start": 3},
    {
        "name": "ui",
        "command": ["streamlit", "run", "ui.py"],
        "dependencies": ["processor", "deployer", "alerter", "allocator"],
        "delay_start": 3,
    },
]

# Global variables to track processes and their states
processes = {}
script_states = {script["name"]: "pending" for script in scripts}
start_times = {}

# Ensure the generated_files directory exists
def ensure_directories_exist():
    """Create necessary directories for log files."""
    try:
        os.makedirs("generated_files", exist_ok=True)
        print("Created 'generated_files' directory")
        return True
    except Exception as e:
        print(f"Failed to create necessary directories: {e}")
        return False

def start_script(script_info):
    """
    Starts a script if its dependencies are met and it's ready to start.
    Returns True if the script was started or is already running, False otherwise.
    """
    name = script_info["name"]
    command = script_info["command"]
    
    # Check if script is already running
    if script_states[name] == "running":
        print(f"{name} is already running")
        return True
        
    # Check if dependencies are met
    dependencies_met = all(
        script_states.get(dep, "stopped") == "running" or script_states.get(dep, "stopped") == "finished"
        for dep in script_info["dependencies"]
    )
    
    # Check if it's time to start the script based on delay
    current_time = time.time()
    if name not in start_times:
        start_times[name] = current_time
    ready_to_start = (current_time - start_times[name]) >= script_info.get("delay_start", 0)
    
    if script_states[name] == "pending" and dependencies_met and ready_to_start:
        print(f"Starting {name}...")
        try:
            # For drift_detector, redirect output to log file
            if name == "drift_detector":
                with open("generated_files/drift_detector_output.log", "a") as log_file:
                    process = subprocess.Popen(
                        command,
                        stdout=log_file,
                        stderr=subprocess.STDOUT
                    )
            else:
                # For others, start normally
                process = subprocess.Popen(command)
                
            processes[name] = process
            script_states[name] = "running"
            print(f"{name} started with PID: {process.pid}")
            return True
        except Exception as e:
            print(f"Failed to start {name}: {e}")
            script_states[name] = "failed"
            return False
    return False

def check_script_status():
    """Checks the status of all running scripts and updates their states."""
    for name, process in list(processes.items()):
        if process.poll() is not None:
            if process.returncode == 0:
                print(f"{name} finished successfully")
                script_states[name] = "finished"
            else:
                print(f"{name} exited with error code {process.returncode}")
                script_states[name] = "failed"
            processes.pop(name)

def stop_script(script_name):
    """Stops a running script and updates its state."""
    if script_name in processes:
        process = processes[script_name]
        try:
            # Try to find all child processes
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            
            # Terminate parent process
            process.terminate()
            
            # Terminate all child processes
            for child in children:
                try:
                    child.terminate()
                except:
                    pass
                    
            print(f"Terminated {script_name}")
            script_states[script_name] = "stopped"
            processes.pop(script_name)
        except Exception as e:
            print(f"Error stopping {script_name}: {e}")
    else:
        print(f"{script_name} is not running")

def stop_all_scripts():
    """Stops all running scripts."""
    for name in list(processes.keys()):
        stop_script(name)

def signal_handler(sig, frame):
    """Handles interrupt signals (Ctrl+C)."""
    print("\nGracefully shutting down all processes...")
    stop_all_scripts()
    sys.exit(0)

def main():
    """Main orchestration function."""
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure directories exist
    if not ensure_directories_exist():
        print("Failed to create necessary directories. Exiting.")
        return
    
    print("Starting the 5G Dynamic Resource Allocation System...")
    
    # Main orchestration loop
    while True:
        # Check status of all scripts
        check_script_status()
        
        # Try to start scripts that are waiting
        for script_info in scripts:
            start_script(script_info)
        
        # Check if all scripts are running or finished
        all_running_or_finished = all(
            state == "running" or state == "finished"
            for state in script_states.values()
        )
        
        if all_running_or_finished:
            # If all scripts are running or finished, just monitor them
            time.sleep(5)
        else:
            # If some scripts are still pending, check more frequently
            time.sleep(1)

if __name__ == "__main__":
    main()