#producer.py
import json
import time
import random
import os
from datetime import datetime


# Ensure the output directory exists
OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_network_data(phase):
    """Generates synthetic network performance data with simulated drift."""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    cell_id = f"Cell-{random.randint(1, 10)}"
    resource_blocks_total = 100

    if phase < 500:
        # Initial phase: Baseline data distribution
        resource_blocks_used = random.randint(10, 90)
        latency_ms = round(random.uniform(5, 50), 2)
        throughput_mbps = round(random.uniform(10, 500), 2)
        active_users = random.randint(50, 500)
    elif 500 <= phase < 1000:
        # Phase 2: Data Drift - Increase in latency and decrease in throughput
        resource_blocks_used = random.randint(30, 95)  # Slightly higher usage
        latency_ms = round(random.uniform(20, 80), 2)
        throughput_mbps = round(random.uniform(5, 200), 2)
        active_users = random.randint(100, 600)
    elif 1000 <= phase < 1500:
        # Phase 3: Concept Drift - Relationship between active users and latency changes
        # Higher active users now lead to significantly higher latency
        resource_blocks_used = random.randint(20, 80)
        active_users = random.randint(150, 700)
        base_latency = round(random.uniform(10, 40), 2)
        latency_ms = base_latency + (active_users / 10)  # Latency influenced by active users
        throughput_mbps = round(random.uniform(20, 400), 2)
    else:
        # Phase 4: Combined Drift - Return to a different data distribution and concept
        resource_blocks_used = random.randint(5, 60) # Lower usage again
        latency_ms = round(random.uniform(15, 65), 2) # Medium latency
        throughput_mbps = round(random.uniform(150, 650), 2) # Higher throughput
        active_users = random.randint(20, 300) # Lower active users, lower latency

    data = {
        "timestamp": timestamp,
        "cell_id": cell_id,
        "resource_blocks_total": resource_blocks_total,
        "resource_blocks_used": resource_blocks_used,
        "latency_ms": latency_ms,
        "throughput_mbps": throughput_mbps,
        "active_users": active_users
    }
    return json.dumps(data)


def write_to_local_file(data, filename="generated_files/network_data.log"):
    """Writes the generated data to a local file."""
    try:
        with open(filename, "a") as f:
            f.write(data + "\n")
        print(f"Data written to {filename}: {data}")
    except Exception as e:
        print(f"Error writing to file {filename}: {e}")


def main():
    """Main function to generate and write network data with simulated drift."""
    phase = 0
    while True:
        network_data = generate_network_data(phase)
        write_to_local_file(network_data)
        time.sleep(random.uniform(0.5, 2))  # Simulate data generation frequency
        phase += 1


if __name__ == "__main__":
    print("Network data producer started.")
    main()
