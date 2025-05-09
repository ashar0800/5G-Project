# processor.py
import json
import time
import os
from datetime import datetime
import pandas as pd


# Define consistent file paths
INPUT_FILENAME = "generated_files/network_data.log"
OUTPUT_FILENAME = "generated_files/processed_features.csv"

# Ensure the output directory exists
OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def read_and_process_data(input_filename=INPUT_FILENAME, output_filename=OUTPUT_FILENAME):
    """Reads data from the log file, processes it, and saves features to a CSV file."""
    processed_data = []
    
    try:
        # Check if input file exists before trying to read
        if not os.path.exists(input_filename):
            print(f"Input file {input_filename} not found. Waiting for data...")
            return
            
        with open(input_filename, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    timestamp = data.get("timestamp")
                    resource_blocks_total = data.get("resource_blocks_total")
                    resource_blocks_used = data.get("resource_blocks_used")

                    if all([timestamp, resource_blocks_total, resource_blocks_used]):
                        utilization_percent = (resource_blocks_used / resource_blocks_total) * 100
                        features = {
                            "timestamp": timestamp,
                            "cell_id": data.get("cell_id"),
                            "latency_ms": data.get("latency_ms"),
                            "throughput_mbps": data.get("throughput_mbps"),
                            "active_users": data.get("active_users"),
                            "resource_block_utilization_percent": utilization_percent
                        }
                        processed_data.append(features)
                    else:
                        print(f"Skipping incomplete data: {line.strip()}")
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {line.strip()}")
                except Exception as e:
                    print(f"An error occurred: {e}")

        if processed_data:
            # Save processed data to CSV
            df = pd.DataFrame(processed_data)
            
            # Save a copy for use as initial baseline data
            if not os.path.exists("generated_files/initial_features.csv"):
                df.to_csv("generated_files/initial_features.csv", index=False)
                print("Initial baseline data saved.")
                
            df.to_csv(output_filename, index=False)
            print(f"Processed features saved to {output_filename}")
        else:
            print("No valid data processed.")
            
    except Exception as e:
        print(f"Error in processing data: {e}")


def main():
    """Main function to continuously read and process network data."""
    print("Data processor started.")
    while True:
        read_and_process_data()
        time.sleep(5)  # Process new data every 5 seconds


if __name__ == "__main__":
    main()
