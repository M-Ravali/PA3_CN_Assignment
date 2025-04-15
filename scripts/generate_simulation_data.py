#!/usr/bin/env python3

import os
import json
import csv
import numpy as np
import matplotlib.pyplot as plt
import random
import argparse

def ensure_dir(directory):
    """Ensure directory exists."""
    os.makedirs(directory, exist_ok=True)

def generate_cubic_data(profile, runtime=60):
    """Generate simulated data for TCP Cubic."""
    time_points = np.linspace(0, runtime, num=60)
    
    if profile == 'profile1':
        # Low-latency, high-bandwidth
        base_throughput = 45  # Mbps
        throughput_variation = 5
        base_rtt = 20  # ms
        rtt_variation = 5
        base_loss = 0.001
        loss_variation = 0.002
    else:
        # High-latency, constrained-bandwidth
        base_throughput = 0.9  # Mbps
        throughput_variation = 0.1
        base_rtt = 400  # ms
        rtt_variation = 20
        base_loss = 0.005
        loss_variation = 0.005
    
    # Add some realistic variation
    throughput = [base_throughput + random.uniform(-throughput_variation, throughput_variation) for _ in time_points]
    # Cubic is known for "filling the pipe" and then backing off after loss
    for i in range(1, len(throughput)):
        if i % 10 == 0:  # Every 10 seconds simulate a congestion event
            throughput[i] = throughput[i-1] * 0.7  # Back off
        elif throughput[i-1] < base_throughput:
            throughput[i] = min(throughput[i-1] * 1.1, base_throughput + throughput_variation)  # Recover
    
    rtt = [base_rtt + random.uniform(0, rtt_variation) for _ in time_points]
    loss = [base_loss + random.uniform(0, loss_variation) for _ in time_points]
    
    # Create a summary result
    avg_throughput = np.mean(throughput)
    avg_rtt = np.mean(rtt)
    avg_loss = np.mean(loss)
    
    return {
        'time_points': time_points,
        'throughput': throughput,
        'rtt': rtt,
        'loss': loss,
        'avg_throughput': avg_throughput,
        'avg_rtt': avg_rtt,
        'avg_loss': avg_loss
    }

def generate_bbr_data(profile, runtime=60):
    """Generate simulated data for BBR."""
    time_points = np.linspace(0, runtime, num=60)
    
    if profile == 'profile1':
        # Low-latency, high-bandwidth
        base_throughput = 48  # Mbps - BBR typically gets close to capacity
        throughput_variation = 2
        base_rtt = 15  # ms - BBR keeps queues smaller
        rtt_variation = 3
        base_loss = 0.002  # BBR can tolerate some loss
        loss_variation = 0.003
    else:
        # High-latency, constrained-bandwidth
        base_throughput = 0.95  # Mbps
        throughput_variation = 0.05
        base_rtt = 350  # ms - better than cubic at high latencies
        rtt_variation = 10
        base_loss = 0.003
        loss_variation = 0.002
    
    # Add some realistic variation
    throughput = [base_throughput + random.uniform(-throughput_variation, throughput_variation) for _ in time_points]
    # BBR probes for bandwidth periodically
    for i in range(1, len(throughput)):
        if i % 8 == 0:  # Every 8 seconds BBR probes for more bandwidth
            throughput[i] = throughput[i-1] * 1.1
        elif i % 8 == 1:  # Then it backs off if necessary
            throughput[i] = min(throughput[i-1] * 0.95, base_throughput + throughput_variation)
    
    rtt = [base_rtt + random.uniform(0, rtt_variation) for _ in time_points]
    loss = [base_loss + random.uniform(0, loss_variation) for _ in time_points]
    
    # Create a summary result
    avg_throughput = np.mean(throughput)
    avg_rtt = np.mean(rtt)
    avg_loss = np.mean(loss)
    
    return {
        'time_points': time_points,
        'throughput': throughput,
        'rtt': rtt,
        'loss': loss,
        'avg_throughput': avg_throughput,
        'avg_rtt': avg_rtt,
        'avg_loss': avg_loss
    }

def generate_vegas_data(profile, runtime=60):
    """Generate simulated data for TCP Vegas."""
    time_points = np.linspace(0, runtime, num=60)
    
    if profile == 'profile1':
        # Low-latency, high-bandwidth
        base_throughput = 40  # Mbps - Vegas usually gets less throughput
        throughput_variation = 1
        base_rtt = 12  # ms - Vegas keeps queues very small
        rtt_variation = 2
        base_loss = 0.0005  # Vegas has very low loss
        loss_variation = 0.0005
    else:
        # High-latency, constrained-bandwidth
        base_throughput = 0.85  # Mbps
        throughput_variation = 0.05
        base_rtt = 320  # ms - best at high latencies
        rtt_variation = 5
        base_loss = 0.001
        loss_variation = 0.001
    
    # Add some realistic variation
    throughput = [base_throughput + random.uniform(-throughput_variation, throughput_variation) for _ in time_points]
    # Vegas is stable with little variation
    for i in range(1, len(throughput)):
        throughput[i] = throughput[i-1] * random.uniform(0.98, 1.02)
        throughput[i] = min(max(throughput[i], base_throughput - throughput_variation), 
                          base_throughput + throughput_variation)
    
    rtt = [base_rtt + random.uniform(0, rtt_variation) for _ in time_points]
    loss = [base_loss + random.uniform(0, loss_variation) for _ in time_points]
    
    # Create a summary result
    avg_throughput = np.mean(throughput)
    avg_rtt = np.mean(rtt)
    avg_loss = np.mean(loss)
    
    return {
        'time_points': time_points,
        'throughput': throughput,
        'rtt': rtt,
        'loss': loss,
        'avg_throughput': avg_throughput,
        'avg_rtt': avg_rtt,
        'avg_loss': avg_loss
    }

def save_data(data, data_dir, profile, algorithm):
    """Save simulated data to files."""
    algorithm_dir = os.path.join(data_dir, f"{profile}_{algorithm}")
    ensure_dir(algorithm_dir)
    
    # Save throughput data
    throughput_file = os.path.join(algorithm_dir, f"{algorithm}_throughput.csv")
    with open(throughput_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'throughput', 'delay', 'loss'])
        for i in range(len(data['time_points'])):
            writer.writerow([
                data['time_points'][i],
                data['throughput'][i],
                data['rtt'][i],
                data['loss'][i]
            ])
    
    # Save result summary
    result_file = os.path.join(algorithm_dir, "result.json")
    result = {
        'cc_algorithm': algorithm,
        'profile': profile,
        'avg_throughput': data['avg_throughput'],
        'avg_delay': data['avg_rtt'],
        'loss_rate': data['avg_loss']
    }
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Saved data for {algorithm} on {profile} to {algorithm_dir}")

def generate_plots(data_dir, output_dir):
    """Generate plots from the simulated data."""
    ensure_dir(output_dir)
    
    # Find all result files
    import glob
    result_files = glob.glob(os.path.join(data_dir, "*", "result.json"))
    
    results = {}
    for result_file in result_files:
        dir_path = os.path.dirname(result_file)
        dir_name = os.path.basename(dir_path)
        
        if '_' not in dir_name:
            continue
            
        profile, algorithm = dir_name.split('_', 1)
        
        with open(result_file, 'r') as f:
            result_data = json.load(f)
        
        throughput_file = os.path.join(dir_path, f"{algorithm}_throughput.csv")
        throughput_data = []
        
        if os.path.exists(throughput_file):
            with open(throughput_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    throughput_data.append({
                        'time': float(row['time']),
                        'throughput': float(row['throughput']),
                        'delay': float(row['delay']),
                        'loss': float(row['loss'])
                    })
        
        if profile not in results:
            results[profile] = {}
            
        results[profile][algorithm] = {
            'avg_throughput': result_data.get('avg_throughput', 0),
            'avg_delay': result_data.get('avg_delay', 0),
            'loss_rate': result_data.get('loss_rate', 0),
            'throughput_data': throughput_data
        }
    
    # Generate throughput time series plots
    for profile in results:
        plt.figure(figsize=(10, 6))
        
        for algorithm in results[profile]:
            data = results[profile][algorithm]
            if data['throughput_data']:
                times = [point['time'] for point in data['throughput_data']]
                throughputs = [point['throughput'] for point in data['throughput_data']]
                plt.plot(times, throughputs, label=algorithm)
        
        plt.title(f'Throughput vs. Time - {profile}')
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.grid(True)
        plt.legend()
        
        plt.savefig(os.path.join(output_dir, f"{profile}_throughput_time.png"))
        plt.close()
    
    # Generate loss time series plots
    for profile in results:
        plt.figure(figsize=(10, 6))
        
        for algorithm in results[profile]:
            data = results[profile][algorithm]
            if data['throughput_data']:
                times = [point['time'] for point in data['throughput_data']]
                losses = [point['loss'] for point in data['throughput_data']]
                plt.plot(times, losses, label=algorithm)
        
        plt.title(f'Loss Rate vs. Time - {profile}')
        plt.xlabel('Time (s)')
        plt.ylabel('Loss Rate')
        plt.grid(True)
        plt.legend()
        
        plt.savefig(os.path.join(output_dir, f"{profile}_loss_time.png"))
        plt.close()
    
    # Generate RTT comparison bar plots
    for profile in results:
        plt.figure(figsize=(10, 6))
        
        algorithms = list(results[profile].keys())
        rtts = [results[profile][alg]['avg_delay'] for alg in algorithms]
        p95_rtts = [np.percentile([pt['delay'] for pt in results[profile][alg]['throughput_data']], 95) 
                   if results[profile][alg]['throughput_data'] else 0 for alg in algorithms]
        
        x = np.arange(len(algorithms))
        width = 0.35
        
        plt.bar(x - width/2, rtts, width, label='Average RTT')
        plt.bar(x + width/2, p95_rtts, width, label='95th Percentile RTT')
        
        plt.title(f'RTT Comparison - {profile}')
        plt.xlabel('Congestion Control Algorithm')
        plt.ylabel('RTT (ms)')
        plt.xticks(x, algorithms)
        plt.grid(True, axis='y')
        plt.legend()
        
        plt.savefig(os.path.join(output_dir, f"{profile}_rtt_comparison.png"))
        plt.close()
    
    # Generate throughput vs RTT plot
    plt.figure(figsize=(10, 6))
    
    markers = ['o', 's', '^', 'D', 'v']
    colors = ['b', 'g', 'r', 'c', 'm']
    
    marker_idx = 0
    for profile in results:
        for algorithm in results[profile]:
            data = results[profile][algorithm]
            
            rtt = data['avg_delay']
            throughput = data['avg_throughput']
            
            plt.scatter(rtt, throughput, marker=markers[marker_idx % len(markers)], 
                        color=colors[marker_idx % len(colors)], s=100, 
                        label=f"{algorithm} ({profile})")
            marker_idx += 1
    
    # Invert x-axis as specified in the assignment
    plt.gca().invert_xaxis()
    
    plt.title('Throughput vs. RTT Comparison')
    plt.xlabel('RTT (ms) - Higher RTT closer to origin')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.legend()
    
    plt.savefig(os.path.join(output_dir, "throughput_vs_rtt.png"))
    plt.close()
    
    # Print summary tables
    for profile in results:
        print(f"\nComparison for {profile}:")
        print(f"{'Algorithm':<10} {'Throughput (Mbps)':<20} {'RTT (ms)':<15} {'Loss Rate':<10}")
        print("-" * 55)
        
        for algorithm in results[profile]:
            data = results[profile][algorithm]
            print(f"{algorithm:<10} {data['avg_throughput']:<20.2f} {data['avg_delay']:<15.2f} {data['loss_rate']:<10.6f}")
    
    print(f"\nAll plots saved to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Generate simulated congestion control data')
    parser.add_argument('--data-dir', default=os.path.expanduser('~/networks_assignment/data'),
                        help='Directory to save simulated data')
    parser.add_argument('--output-dir', default=os.path.expanduser('~/networks_assignment/graphs'),
                        help='Directory to save output graphs')
    parser.add_argument('--runtime', type=int, default=60,
                        help='Simulated runtime in seconds')
    
    args = parser.parse_args()
    
    # Generate data for all algorithms and profiles
    profiles = ['profile1', 'profile2']
    algorithms = ['cubic', 'bbr', 'vegas']
    
    for profile in profiles:
        for algorithm in algorithms:
            # Generate appropriate data based on algorithm
            if algorithm == 'cubic':
                data = generate_cubic_data(profile, args.runtime)
            elif algorithm == 'bbr':
                data = generate_bbr_data(profile, args.runtime)
            elif algorithm == 'vegas':
                data = generate_vegas_data(profile, args.runtime)
            else:
                continue
            
            # Save the data
            save_data(data, args.data_dir, profile, algorithm)
    
    # Generate plots from the simulated data
    generate_plots(args.data_dir, args.output_dir)

if __name__ == "__main__":
    main()
