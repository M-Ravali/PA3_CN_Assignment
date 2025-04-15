#!/usr/bin/env python3

import os
import subprocess
import time
import argparse
import json
import csv
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def run_command(cmd, log_file=None):
    """Run a command and optionally log its output."""
    print(f"Running: {cmd}")
    
    if log_file:
        with open(log_file, 'w') as f:
            process = subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.STDOUT)
    else:
        process = subprocess.Popen(cmd, shell=True)
        
    process.wait()
    return process.returncode

def get_available_cc_algorithms():
    """Get list of available congestion control algorithms on the system."""
    try:
        with open('/proc/sys/net/ipv4/tcp_available_congestion_control', 'r') as f:
            algorithms = f.read().strip().split()
            return algorithms
    except:
        # Default to these common ones if can't read from proc
        return ['cubic', 'bbr', 'vegas']

def setup_tc(interface, bandwidth_mbps, delay_ms, queue_size_bytes):
    """Set up traffic control on the specified interface."""
    # Clear any existing qdisc
    run_command(f"sudo tc qdisc del dev {interface} root 2>/dev/null")
    
    # Set up HTB with rate limit
    run_command(f"sudo tc qdisc add dev {interface} root handle 1: htb default 10")
    run_command(f"sudo tc class add dev {interface} parent 1: classid 1:10 htb rate {bandwidth_mbps}mbit")
    
    # Add delay and queue size limitation
    run_command(f"sudo tc qdisc add dev {interface} parent 1:10 handle 10: netem delay {delay_ms}ms limit {queue_size_bytes}")
    
    print(f"Set up traffic control on {interface}: {bandwidth_mbps}Mbps, {delay_ms}ms delay, {queue_size_bytes} queue size")

def cleanup_tc(interface):
    """Clean up traffic control settings."""
    run_command(f"sudo tc qdisc del dev {interface} root 2>/dev/null")
    print(f"Cleaned up traffic control on {interface}")

def run_experiment(cc_algorithm, profile, runtime=60):
    """Run experiment for a specific congestion control algorithm and network profile."""
    base_dir = os.path.expanduser('~/networks_assignment')
    data_dir = f"{base_dir}/data/{profile}_{cc_algorithm}"
    log_dir = f"{base_dir}/logs"
    
    # Create directories if they don't exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/{profile}_{cc_algorithm}.log"
    results_file = f"{data_dir}/result.json"
    throughput_file = f"{data_dir}/{cc_algorithm}_throughput.csv"
    
    # Set up network profile parameters
    if profile == 'profile1':  # Low-latency, high-bandwidth
        delay_ms = 10
        bandwidth_mbps = 50
        queue_size_bytes = int(bandwidth_mbps * 1000000 * delay_ms / 8 / 1000)  # BDP in bytes
    elif profile == 'profile2':  # High-latency, constrained-bandwidth
        delay_ms = 200
        bandwidth_mbps = 1
        queue_size_bytes = int(bandwidth_mbps * 1000000 * delay_ms / 8 / 1000)  # BDP in bytes
    else:
        print(f"Unknown profile: {profile}")
        return 1
    
    # Get default interface
    interface = subprocess.check_output("ip route | grep default | awk '{print $5}'", shell=True).decode().strip()
    if not interface:
        print("Could not determine default network interface")
        return 1
    
    print(f"Using network interface: {interface}")
    
    # Set congestion control algorithm
    run_command(f"sudo sysctl -w net.ipv4.tcp_congestion_control={cc_algorithm}")
    print(f"Set congestion control algorithm to {cc_algorithm}")
    
    try:
        # Set up traffic control
        setup_tc(interface, bandwidth_mbps, delay_ms, queue_size_bytes)
        
        # Set up iperf server in the background
        server_port = 5050
        run_command(f"iperf3 -s -p {server_port} -D")
        
        # Run iperf client with JSON output
        iperf_cmd = f"iperf3 -c localhost -p {server_port} -t {runtime} -J > {data_dir}/iperf_result.json"
        run_command(iperf_cmd)
        
        # Process results
        with open(f"{data_dir}/iperf_result.json", 'r') as f:
            iperf_data = json.load(f)
        
        # Extract data
        intervals = iperf_data.get('intervals', [])
        
        # Prepare throughput data
        throughput_data = []
        
        total_throughput = 0
        total_retransmits = 0
        total_bytes = 0
        
        # Process each interval
        for interval in intervals:
            sum_data = interval.get('sum', {})
            
            seconds = sum_data.get('seconds', 0)
            bytes_transferred = sum_data.get('bytes', 0)
            retransmits = sum_data.get('retransmits', 0)
            
            # Calculate throughput in Mbps
            throughput = (bytes_transferred * 8) / (seconds * 1000000) if seconds > 0 else 0
            
            # Calculate approximate packet loss based on retransmits
            # Assuming 1500-byte packets
            packets_sent = bytes_transferred / 1500 if bytes_transferred > 0 else 1
            loss_rate = retransmits / packets_sent if packets_sent > 0 else 0
            
            # Save interval data
            throughput_data.append({
                'time': sum_data.get('start', 0),
                'throughput': throughput,
                'delay': delay_ms * 2,  # RTT is roughly 2x the delay
                'loss': loss_rate
            })
            
            total_throughput += throughput
            total_retransmits += retransmits
            total_bytes += bytes_transferred
        
        # Calculate averages
        num_intervals = len(intervals)
        avg_throughput = total_throughput / num_intervals if num_intervals > 0 else 0
        total_packets = total_bytes / 1500 if total_bytes > 0 else 1
        avg_loss_rate = total_retransmits / total_packets if total_packets > 0 else 0
        
        # Save results
        result = {
            'cc_algorithm': cc_algorithm,
            'profile': profile,
            'avg_throughput': avg_throughput,
            'avg_delay': delay_ms * 2,  # RTT is roughly 2x the delay
            'loss_rate': avg_loss_rate
        }
        
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save throughput data
        with open(throughput_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['time', 'throughput', 'delay', 'loss'])
            writer.writeheader()
            for data in throughput_data:
                writer.writerow(data)
        
        print(f"Experiment completed successfully for {cc_algorithm} on {profile}")
        print(f"Average throughput: {avg_throughput:.2f} Mbps")
        print(f"Average RTT: {delay_ms * 2:.2f} ms")
        print(f"Loss rate: {avg_loss_rate:.4f}")
        
        return 0
    
    except Exception as e:
        print(f"Error during experiment: {e}")
        return 1
    
    finally:
        # Clean up
        cleanup_tc(interface)
        run_command("killall -9 iperf3 2>/dev/null")

def main():
    parser = argparse.ArgumentParser(description='Run traffic control experiments')
    parser.add_argument('--schemes', nargs='+', default=['cubic', 'bbr', 'vegas'],
                      help='Congestion control schemes to test')
    parser.add_argument('--profiles', nargs='+', default=['profile1', 'profile2'],
                      help='Network profiles to test')
    parser.add_argument('--runtime', type=int, default=60,
                      help='Runtime for each experiment in seconds')
    
    args = parser.parse_args()
    
    # Check available congestion control algorithms
    available_algorithms = get_available_cc_algorithms()
    print(f"Available congestion control algorithms: {', '.join(available_algorithms)}")
    
    # Filter schemes to only those available
    schemes = [scheme for scheme in args.schemes if scheme in available_algorithms]
    
    if not schemes:
        print("Error: None of the specified congestion control algorithms are available!")
        return 1
    
    # Run experiments
    for scheme in schemes:
        for profile in args.profiles:
            print(f"\n===== Running experiment: {scheme} on {profile} =====\n")
            result = run_experiment(scheme, profile, args.runtime)
            if result != 0:
                print(f"Experiment failed for {scheme} on {profile}")
    
    print("All experiments completed!")
    return 0

if __name__ == "__main__":
    main()
