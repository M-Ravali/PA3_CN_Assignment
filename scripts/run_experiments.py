#!/usr/bin/env python3

import os
import subprocess
import sys
import time
import argparse
from multiprocessing import Pool

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

def run_single_experiment(scheme, profile, runtime=60):
    """Run an experiment for a single CC scheme under a specific network profile."""
    base_dir = os.path.expanduser('~/networks_assignment')
    pantheon_dir = os.path.join(base_dir, 'pantheon')
    data_dir = f"{base_dir}/data/{profile}_{scheme}"
    log_file = f"{base_dir}/logs/{profile}_{scheme}.log"
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # Parse the profile configuration
    if profile == 'profile1':  # Low-latency, high-bandwidth
        delay_ms = 10
        bandwidth_mbps = 50
        queue_size_bytes = 62500  # BDP: 50 Mbps * 10 ms = 62500 bytes
        trace_file = f"{base_dir}/traces/50mbps.trace"
    elif profile == 'profile2':  # High-latency, constrained-bandwidth
        delay_ms = 200
        bandwidth_mbps = 1
        queue_size_bytes = 25000  # BDP: 1 Mbps * 200 ms = 25000 bytes
        trace_file = f"{base_dir}/traces/1mbps.trace"
    else:
        print(f"Unknown profile: {profile}")
        return 1
    
    # Change to pantheon directory
    os.chdir(pantheon_dir)
    
    # Check if the scheme is installed
    check_cmd = f"./src/experiments/test.py --run-only --schemes {scheme} --dry-run"
    ret = run_command(check_cmd)
    if ret != 0:
        print(f"Scheme {scheme} is not available. Installing...")
        install_cmd = f"./src/experiments/setup.py --schemes {scheme}"
        run_command(install_cmd)
    
    # Construct the test command
    cmd = (
        f"./src/experiments/test.py --run-only --schemes {scheme} "
        f"--data-dir {data_dir} --runtime {runtime} "
        f"--uplink-trace {trace_file} --downlink-trace {trace_file} "
        f"--extra-mm-cmd=\"mm-delay {delay_ms}\" "
        f"--extra-mm-link-args=\"--uplink-queue=droptail --uplink-queue-args=bytes={queue_size_bytes} "
        f"--downlink-queue=droptail --downlink-queue-args=bytes={queue_size_bytes}\" "
        f"--pkill-cleanup local"
    )
    
    # Run the experiment
    ret = run_command(cmd, log_file)
    if ret != 0:
        print(f"Experiment failed for {scheme} on {profile}")
        return ret
    
    # Analyze the results
    analyze_cmd = f"./src/analysis/analyze.py --data-dir {data_dir}"
    ret = run_command(analyze_cmd, log_file + '.analyze')
    
    print(f"Completed experiment for {scheme} on {profile}")
    return ret

def main():
    parser = argparse.ArgumentParser(description='Run Pantheon experiments')
    parser.add_argument('--schemes', nargs='+', default=['cubic', 'bbr', 'vegas'],
                        help='Congestion control schemes to test')
    parser.add_argument('--profiles', nargs='+', default=['profile1', 'profile2'],
                        help='Network profiles to test')
    parser.add_argument('--runtime', type=int, default=60,
                        help='Runtime for each experiment in seconds')
    parser.add_argument('--parallel', type=int, default=1,
                        help='Number of experiments to run in parallel')
    
    args = parser.parse_args()
    
    # Prepare experiment combinations
    experiments = []
    for scheme in args.schemes:
        for profile in args.profiles:
            experiments.append((scheme, profile, args.runtime))
    
    # Run experiments in parallel or sequentially
    if args.parallel > 1:
        with Pool(args.parallel) as p:
            results = p.starmap(run_single_experiment, experiments)
    else:
        results = []
        for exp in experiments:
            results.append(run_single_experiment(*exp))
    
    # Check if all experiments succeeded
    if all(r == 0 for r in results):
        print("All experiments completed successfully!")
        return 0
    else:
        print("Some experiments failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())#!/usr/bin/env python3

import os
import subprocess
import sys
import time
import argparse
from multiprocessing import Pool

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

def run_single_experiment(scheme, profile, runtime=60):
    """Run an experiment for a single CC scheme under a specific network profile."""
    base_dir = os.path.expanduser('~/networks_assignment')
    pantheon_dir = os.path.join(base_dir, 'pantheon')
    data_dir = f"{base_dir}/data/{profile}_{scheme}"
    log_file = f"{base_dir}/logs/{profile}_{scheme}.log"
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # Parse the profile configuration
    if profile == 'profile1':  # Low-latency, high-bandwidth
        delay_ms = 10
        bandwidth_mbps = 50
        queue_size_bytes = 62500  # BDP: 50 Mbps * 10 ms = 62500 bytes
        trace_file = f"{base_dir}/traces/50mbps.trace"
    elif profile == 'profile2':  # High-latency, constrained-bandwidth
        delay_ms = 200
        bandwidth_mbps = 1
        queue_size_bytes = 25000  # BDP: 1 Mbps * 200 ms = 25000 bytes
        trace_file = f"{base_dir}/traces/1mbps.trace"
    else:
        print(f"Unknown profile: {profile}")
        return 1
    
    # Change to pantheon directory
    os.chdir(pantheon_dir)
    
    # Construct the test command
    cmd = (
        f"./src/experiments/test.py --run-only --schemes {scheme} "
        f"--data-dir {data_dir} --runtime {runtime} "
        f"--extra-mm-cmd=\"mm-delay {delay_ms}\" "
        f"--uplink-trace {trace_file} --downlink-trace {trace_file} "
        f"--extra-mm-link-args=\"--uplink-queue=droptail --uplink-queue-args=bytes={queue_size_bytes} "
        f"--downlink-queue=droptail --downlink-queue-args=bytes={queue_size_bytes}\" "
        f"--pkill-cleanup local"
    )
    
    # Run the experiment
    ret = run_command(cmd, log_file)
    if ret != 0:
        print(f"Experiment failed for {scheme} on {profile}")
        return ret
    
    # Analyze the results
    analyze_cmd = f"./src/analysis/analyze.py --data-dir {data_dir}"
    ret = run_command(analyze_cmd, log_file + '.analyze')
    
    print(f"Completed experiment for {scheme} on {profile}")
    return ret

def main():
    parser = argparse.ArgumentParser(description='Run Pantheon experiments')
    parser.add_argument('--schemes', nargs='+', default=['cubic', 'bbr', 'vegas'],
                        help='Congestion control schemes to test')
    parser.add_argument('--profiles', nargs='+', default=['profile1', 'profile2'],
                        help='Network profiles to test')
    parser.add_argument('--runtime', type=int, default=60,
                        help='Runtime for each experiment in seconds')
    parser.add_argument('--parallel', type=int, default=1,
                        help='Number of experiments to run in parallel')
    
    args = parser.parse_args()
    
    # Prepare experiment combinations
    experiments = []
    for scheme in args.schemes:
        for profile in args.profiles:
            experiments.append((scheme, profile, args.runtime))
    
    # Run experiments in parallel or sequentially
    if args.parallel > 1:
        with Pool(args.parallel) as p:
            results = p.starmap(run_single_experiment, experiments)
    else:
        results = []
        for exp in experiments:
            results.append(run_single_experiment(*exp))
    
    # Check if all experiments succeeded
    if all(r == 0 for r in results):
        print("All experiments completed successfully!")
        return 0
    else:
        print("Some experiments failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
