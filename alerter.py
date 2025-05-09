# alerter.py
import time
import os
from datetime import datetime


# Configuration: File paths and operational parameters
DRIFT_DETECTOR_LOG_FILENAME = "generated_files/drift_detector_output.log"
ALERTS_LOG_FILENAME = "generated_files/alerts.log"
CHECK_INTERVAL_SECONDS = 10  # How often to check for new drift messages


# To keep track of the last processed line number in the drift detector log
last_processed_line_number = 0


def create_alert_message(drift_log_line):
    """
    Creates a formatted alert message from a drift detector log line.
    Returns the alert message string or None if the line doesn't indicate a notable drift.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    alert_prefix = f"{timestamp} - ALERT: "

    # Standardize the drift message for the alert log
    if "Data drift detected for feature:" in drift_log_line:
        # Example: "Data drift detected for feature: latency_ms (PSI: 0.1234 > 0.1)"
        # We want to capture the core information.
        try:
            # Extract relevant parts
            parts = drift_log_line.split("Data drift detected for feature:")[1].split("(PSI:")
            feature = parts[0].strip()
            psi_info = parts[1].split(">")[0].strip()  # Get just the PSI value
            return f"{alert_prefix}Data drift detected for feature '{feature}' (PSI: {psi_info})."
        except IndexError:
            # Fallback if parsing fails
            return f"{alert_prefix}Data drift detected. Details: {drift_log_line.strip()}"

    elif "Concept drift detected MSE" in drift_log_line:
        # Example: "Concept drift detected MSE (12.3456) exceeds threshold (10.0)"
        try:
            mse_info = drift_log_line.split("MSE (")[1].split(")")[0].strip()
            return f"{alert_prefix}Concept drift detected (MSE: {mse_info})."
        except IndexError:
            # Fallback if parsing fails
            return f"{alert_prefix}Concept drift detected. Details: {drift_log_line.strip()}"

    # Add more conditions here if drift_detector.py logs other types of critical alerts

    return None  # Not a line we want to generate an alert for


def write_to_alerts_log(message):
    """
    Appends the given alert message to the ALERTS_LOG_FILENAME.
    """
    try:
        # Ensure the directory for the log file exists
        os.makedirs(os.path.dirname(ALERTS_LOG_FILENAME), exist_ok=True)
        with open(ALERTS_LOG_FILENAME, "a") as f:
            f.write(message + "\n")
        print(f"Alert logged: {message}")
    except Exception as e:
        print(f"Error writing to alerts log '{ALERTS_LOG_FILENAME}': {e}")


def check_for_new_drift_events():
    """
    Checks the drift detector log for new drift events since the last check
    and logs alerts if any are found.
    """
    global last_processed_line_number
    new_alerts_generated = False
    try:
        # Check if the drift detector log file exists and is not empty
        if not os.path.exists(DRIFT_DETECTOR_LOG_FILENAME):
            print(f"Drift detector log file {DRIFT_DETECTOR_LOG_FILENAME} not found. It will be created when drift_detector.py detects drift")
            return False

        if os.path.getsize(DRIFT_DETECTOR_LOG_FILENAME) == 0:
            print(f"Drift detector log file {DRIFT_DETECTOR_LOG_FILENAME} is empty.")
            return False

        with open(DRIFT_DETECTOR_LOG_FILENAME, "r") as f:
            lines = f.readlines()
        current_line_count = len(lines)

        if current_line_count > last_processed_line_number:
            # Process new lines
            new_lines = lines[last_processed_line_number:]
            print(f"Found {len(new_lines)} new lines in {DRIFT_DETECTOR_LOG_FILENAME}.")
            for line in new_lines:
                stripped_line = line.strip()
                if stripped_line:  # Ensure line is not empty
                    alert_message = create_alert_message(stripped_line)
                    if alert_message:
                        write_to_alerts_log(alert_message)
                        new_alerts_generated = True
            last_processed_line_number = current_line_count
    except FileNotFoundError:
        print(f"Drift detector log file {DRIFT_DETECTOR_LOG_FILENAME} not found. It will be created when drift_detector.py detects drift")
        return False
    except Exception as e:
        print(f"Error reading drift detector log '{DRIFT_DETECTOR_LOG_FILENAME}': {e}")
        return False
    return new_alerts_generated


def main():
    """
    Main function for the alerter.
    Continuously monitors the drift detector log and generates alerts.
    """
    print("Alerter service started. Monitoring for drift detection events...")

    # Ensure log directories exist
    try:
        os.makedirs(os.path.dirname(DRIFT_DETECTOR_LOG_FILENAME), exist_ok=True)
        os.makedirs(os.path.dirname(ALERTS_LOG_FILENAME), exist_ok=True)
        print("Log directories created successfully.")
    except OSError as e:
        print(f"Error creating log directories: {e}. Please ensure the program has write permissions.")
        return  # Exit if directories cannot be created

    while True:
        try:
            check_for_new_drift_events()
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("Alerter service shutting down due to KeyboardInterrupt.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the alerter main loop: {e}")
            time.sleep(CHECK_INTERVAL_SECONDS * 2)


if __name__ == "__main__":
    main()
