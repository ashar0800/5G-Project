import streamlit as st
import pandas as pd
import time
import json
import re
from datetime import datetime
import os
import subprocess

# Configuration Files
PREDICTIONS_LOG_FILENAME = "generated_files/predictions.log"
ALERTS_LOG_FILENAME = "generated_files/alerts.log"
ALLOCATION_LOG_FILENAME = "generated_files/allocation.log"
NETWORK_DATA_LOG_FILENAME = "generated_files/network_data.log"
DRIFT_DETECTOR_LOG_FILENAME = "generated_files/drift_detector_output.log"
PROCESSED_FEATURES_FILENAME = "generated_files/processed_features.csv"

# Default parameter values
DEFAULT_DRIFT_THRESHOLD_PSI = 0.1
DEFAULT_CONCEPT_DRIFT_MSE_THRESHOLD = 10.0
DEFAULT_HIGH_UTILIZATION_THRESHOLD = 85.0
DEFAULT_LOW_UTILIZATION_THRESHOLD = 30.0

def load_latest_data(filename, parser_function=lambda x: x):
    try:
        if not os.path.exists(filename):
            return None
        with open(filename, "r") as f:
            lines = f.readlines()
            if lines:
                return parser_function(lines[-1].strip())
    except Exception as e:
        st.error(f"Error loading data from {filename}: {e}")
        return None
    return None

def parse_network_data(line):
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None

def get_latest_prediction():
    line = load_latest_data(PREDICTIONS_LOG_FILENAME)
    if line:
        match = re.search(r"Cell ID: (.*?), Predicted Utilization: (.*?)\%", line)
        if match:
            return match.group(1).strip(), float(match.group(2).strip())
    return None, None

def get_latest_alert():
    return load_latest_data(ALERTS_LOG_FILENAME)

def get_latest_allocation():
    return load_latest_data(ALLOCATION_LOG_FILENAME)

def read_log_file(filename, max_lines=100):
    try:
        if not os.path.exists(filename):
            return ["Log file not found."]
        with open(filename, "r") as f:
            lines = f.readlines()
            return lines[-max_lines:] if lines else ["No data in log file."]
    except Exception as e:
        return [f"Error reading log file: {e}"]

def is_script_running(script_name):
    try:
        if os.name == 'nt':
            tasks = subprocess.check_output(['tasklist'], creationflags=subprocess.CREATE_NO_WINDOW, text=True)
            return f"python*{script_name}.py" in tasks
        else:
            processes = subprocess.check_output(['pgrep', '-f', f"{script_name}.py"], text=True)
            return script_name in processes
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        st.error(f"Error checking script status for {script_name}: {e}")
        return False

def ensure_directories_exist():
    try:
        os.makedirs("generated_files", exist_ok=True)
        return True
    except Exception as e:
        st.error(f"Failed to create necessary directories: {e}")
        return False

def load_processed_features(max_rows=50):
    try:
        if not os.path.exists(PROCESSED_FEATURES_FILENAME):
            return None
        df = pd.read_csv(PROCESSED_FEATURES_FILENAME)
        if df.empty:
            return None
        return df.tail(max_rows)
    except Exception as e:
        st.error(f"Error loading processed features: {e}")
        return None

def main():
    ensure_directories_exist()

    st.title("5G Dynamic Resource Allocation Simulation Dashboard")

    # Sidebar controls
    st.sidebar.header("Simulation Controls")

    drift_threshold_psi = st.sidebar.slider(
        "Drift Threshold (PSI)", 0.01, 0.5, DEFAULT_DRIFT_THRESHOLD_PSI, 0.01
    )
    concept_drift_mse_threshold = st.sidebar.number_input(
        "Concept Drift Threshold (MSE)", 1.0, 20.0, DEFAULT_CONCEPT_DRIFT_MSE_THRESHOLD, 0.1
    )
    high_utilization_threshold = st.sidebar.slider(
        "High Utilization Threshold (%)", 50.0, 100.0, DEFAULT_HIGH_UTILIZATION_THRESHOLD, 1.0
    )
    low_utilization_threshold = st.sidebar.slider(
        "Low Utilization Threshold (%)", 0.0, 50.0, DEFAULT_LOW_UTILIZATION_THRESHOLD, 1.0
    )

    # Current metrics
    st.subheader("Current Network Status")
    col1, col2, col3 = st.columns(3)

    latest_network_data = load_latest_data(NETWORK_DATA_LOG_FILENAME, parse_network_data)
    if latest_network_data:
        cell_id = latest_network_data.get("cell_id", "N/A")
        resource_blocks_used = latest_network_data.get("resource_blocks_used", 0)
        resource_blocks_total = latest_network_data.get("resource_blocks_total", 1)

        utilization = (
            round(resource_blocks_used / resource_blocks_total * 100, 2)
            if resource_blocks_total > 0 else "N/A"
        )
        latency = latest_network_data.get("latency_ms", "N/A")
        throughput = latest_network_data.get("throughput_mbps", "N/A")

        col1.metric("Cell ID", cell_id)
        col2.metric("Utilization (%)", utilization)
        col3.metric("Latency (ms)", latency)

        col1, col2, col3 = st.columns(3)
        col1.metric("Throughput (Mbps)", throughput)
        col2.metric("Active Users", latest_network_data.get("active_users", "N/A"))

    prediction_cell, predicted_utilization = get_latest_prediction()
    if prediction_cell:
        st.metric(f"Predicted Util. ({prediction_cell}) (%)", f"{predicted_utilization:.2f}")

    latest_alert = get_latest_alert()
    if latest_alert:
        st.warning(f"Latest Alert: {latest_alert}")

    latest_allocation = get_latest_allocation()
    if latest_allocation:
        st.info(f"Latest Allocation: {latest_allocation}")

    # Log viewer
    st.subheader("Log Data")
    log_file_selection = st.selectbox(
        "Select Log File",
        ["Predictions", "Alerts", "Allocation", "Network Data", "Drift Detector"]
    )
    log_files = {
        "Predictions": PREDICTIONS_LOG_FILENAME,
        "Alerts": ALERTS_LOG_FILENAME,
        "Allocation": ALLOCATION_LOG_FILENAME,
        "Network Data": NETWORK_DATA_LOG_FILENAME,
        "Drift Detector": DRIFT_DETECTOR_LOG_FILENAME,
    }
    log_lines = read_log_file(log_files[log_file_selection], max_lines=100)
    st.text_area(f"{log_file_selection} Log", value="\n".join(log_lines), height=400)

    # Historical charts
    st.subheader("Historical Trends")
    df_features = load_processed_features(max_rows=50)

    tab1, tab2 = st.tabs(["Raw Network Data", "Processed Features"])

    with tab1:
        try:
            historical_data = []
            with open(NETWORK_DATA_LOG_FILENAME, "r") as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    try:
                        data = json.loads(line.strip())
                        historical_data.append(data)
                    except json.JSONDecodeError:
                        pass
            if historical_data:
                df_network_history = pd.DataFrame(historical_data)
                if (
                    "timestamp" in df_network_history.columns and
                    "resource_blocks_used" in df_network_history.columns and
                    "resource_blocks_total" in df_network_history.columns
                ):
                    df_network_history["utilization_percent"] = (
                        df_network_history["resource_blocks_used"]
                        / df_network_history["resource_blocks_total"]
                        * 100
                    )
                    df_network_history["timestamp"] = pd.to_datetime(df_network_history["timestamp"])
                    st.line_chart(
                        df_network_history.set_index("timestamp")[[
                            "utilization_percent", "latency_ms", "throughput_mbps"
                        ]]
                    )
        except Exception as e:
            st.error(f"Error processing historical data: {e}")

    with tab2:
        if df_features is not None and not df_features.empty:
            if "timestamp" in df_features.columns:
                df_features["timestamp"] = pd.to_datetime(df_features["timestamp"])
                df_features = df_features.set_index("timestamp")

            if "resource_block_utilization_percent" in df_features.columns:
                st.line_chart(df_features["resource_block_utilization_percent"])

            if all(col in df_features.columns for col in ["latency_ms", "throughput_mbps", "active_users"]):
                st.line_chart(df_features[["latency_ms", "throughput_mbps", "active_users"]])
        else:
            st.warning("No processed feature data available for visualization.")

    st.checkbox("Auto-refresh (5s)", value=True, key="auto_refresh")

    if st.session_state.get("auto_refresh", True):
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
