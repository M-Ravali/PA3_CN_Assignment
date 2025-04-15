#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import json
import argparse
from collections import defaultdict

def parse_pantheon_logs(data_dir):
    """Parse Pantheon log files and extract performance metrics."""
    results = {}
    
    # Find all experiment directories
    experiment_dirs = [d for d in glob.glob(f"{data_dir}/*_*") if os.path.isdir(d)]
    
    for exp_dir in experiment_dirs:
        # Extract profile and scheme from directory name
        dirname = os.path.basename(exp_dir)
        parts = dirname.split('_')
        if len(parts) < 2:
            continue
            
        profile, scheme = parts[0], parts[1]
        
        # Check if results exist
        if not os.path.exists(f"{exp_dir}/result.json"):
            print(f"No results found for {profile}_{scheme}")
            continue
        
        # Load results
        with open(f"{exp_dir}/result.json", 'r') as f:
            result_data = json.load(f)
        
        # Load throughput data
        throughput_file = f"{exp_dir}/{scheme}_throughput.csv"
        if not os.path.exists(throughput_file):
            # Try alternate filename
            throughput_file = f"{exp_dir}/throughput.csv"
            if not os.path.exists(throughput_file):
                print(f"No throughput data found for {profile}_{scheme}")
                continue
            
        throughput_data = pd.read_csv(throughput_file)
        
        # Calculate statistics
        avg_throughput = result_data.get('avg_throughput', 0)
        avg_delay = result_data.get('avg_delay', 0)
        loss_rate = result_data.get('loss_rate', 0)
        
        # Calculate 95th percentile of delay if available
        if 'delay' in throughput_data.columns:
            p95_delay = np.percentile(throughput_data['delay'], 95)
        else:
            p95_delay = 0
        
        # Store results
        if profile not in results:
            results[profile] = {}
            
        results[profile][scheme] = {
            'avg_throughput': avg_throughput,
            'avg_delay': avg_delay,
            'p95_delay': p95_delay,
            'loss_rate': loss_rate,
            'throughput_data': throughput_data
        }
    
    return results

def plot_throughput_time_series(results, output_dir):
    """Plot time-series throughput for each CC scheme and network profile."""
    for profile, schemes_data in results.items():
        plt.figure(figsize=(10, 6))
        
        for scheme, data in schemes_data.items():
            throughput_data = data['throughput_data']
            if 'time' in throughput_data.columns and 'throughput' in throughput_data.columns:
                plt.plot(throughput_data['time'], throughput_data['throughput'], label=scheme)
        
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.title(f'Throughput vs. Time - {profile}')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/{profile}_throughput_time.png")
        plt.close()

def plot_loss_time_series(results, output_dir):
    """Plot time-series loss rate for each CC scheme and network profile."""
    for profile, schemes_data in results.items():
        plt.figure(figsize=(10, 6))
        
        for scheme, data in schemes_data.items():
            throughput_data = data['throughput_data']
            if 'time' in throughput_data.columns and 'loss' in throughput_data.columns:
                plt.plot(throughput_data['time'], throughput_data['loss'], label=scheme)
        
        plt.xlabel('Time (s)')
        plt.ylabel('Loss Rate')
        plt.title(f'Loss Rate vs. Time - {profile}')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/{profile}_loss_time.png")
        plt.close()

def plot_delay_comparison(results, output_dir):
    """Generate bar plots comparing average and 95th percentile RTT."""
    for profile, schemes_data in results.items():
        avg_delays = []
        p95_delays = []
        scheme_names = []
        
        for scheme, data in schemes_data.items():
            avg_delays.append(data['avg_delay'])
            p95_delays.append(data['p95_delay'])
            scheme_names.append(scheme)
        
        if not scheme_names:
            continue
            
        # Create grouped bar chart
        x = np.arange(len(scheme_names))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x - width/2, avg_delays, width, label='Average RTT')
        ax.bar(x + width/2, p95_delays, width, label='95th Percentile RTT')
        
        ax.set_xlabel('Congestion Control Scheme')
        ax.set_ylabel('RTT (ms)')
        ax.set_title(f'RTT Comparison - {profile}')
        ax.set_xticks(x)
        ax.set_xticklabels(scheme_names)
        ax.legend()
        ax.grid(True, axis='y')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{profile}_rtt_comparison.png")
        plt.close()

def plot_throughput_vs_rtt(results, output_dir):
    """Generate throughput vs RTT scatter plot."""
    plt.figure(figsize=(10, 8))
    
    markers = ['o', 's', 'd', '^', 'v', '<', '>', 'p', '*']
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'orange', 'purple']
    
    points = []
    labels = []
    legend_entries = {}
    
    for profile, schemes_data in results.items():
        for i, (scheme, data) in enumerate(schemes_data.items()):
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            
            rtt = data['avg_delay']
            throughput = data['avg_throughput']
            
            label = f"{scheme} ({profile})"
            if label not in legend_entries:
                legend_entries[label] = (marker, color)
                
            plt.scatter(rtt, throughput, marker=marker, color=color, s=100, label=label)
    
    # Invert x-axis as specified in the assignment
    plt.gca().invert_xaxis()
    
    plt.title('Throughput vs. RTT Comparison')
    plt.xlabel('RTT (ms) - Higher RTT closer to origin')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    
    # Create legend with unique entries
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='best')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/throughput_vs_rtt.png")
    plt.close()

def generate_comparison_table(results, output_dir):
    """Generate comparison tables in CSV format."""
    for profile, schemes_data in results.items():
        # Create a DataFrame for the comparison
        data = []
        for scheme, metrics in schemes_data.items():
            data.append({
                'Scheme': scheme,
                'Avg Throughput (Mbps)': metrics['avg_throughput'],
                'Avg RTT (ms)': metrics['avg_delay'],
                '95th Percentile RTT (ms)': metrics['p95_delay'],
                'Loss Rate (%)': metrics['loss_rate'] * 100
            })
        
        if not data:
            continue
            
        df = pd.DataFrame(data)
        
        # Save to CSV
        csv_file = f"{output_dir}/{profile}_comparison.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved comparison table to {csv_file}")
        
        # Also print to console
        print(f"\nComparison for {profile}:")
        print(df.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='Analyze Pantheon experiment results')
    parser.add_argument('--data-dir', default=os.path.expanduser('~/networks_assignment/data'),
                      help='Directory containing experimental data')
    parser.add_argument('--output-dir', default=os.path.expanduser('~/networks_assignment/graphs'),
                      help='Directory to save output graphs')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Parse experiment results
    results = parse_pantheon_logs(args.data_dir)
    
    if not results:
        print("No experiment results found. Make sure experiments have been run.")
        return 1
    
    # Generate plots
    plot_throughput_time_series(results, args.output_dir)
    plot_loss_time_series(results, args.output_dir)
    plot_delay_comparison(results, args.output_dir)
    plot_throughput_vs_rtt(results, args.output_dir)
    
    # Generate comparison tables
    generate_comparison_table(results, args.output_dir)
    
    print("\nAnalysis complete! Graphs saved to:", args.output_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())bps)')
        plt.title(f'Throughput vs. Time - {profile}')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/{profile}_throughput_time.png")
        plt.close()

def plot_loss_time_series(results, output_dir):
    """Plot time-series loss rate for each CC scheme and network profile."""
    for profile, schemes_data in results.items():
        plt.figure(figsize=(10, 6))
        
        for scheme, data in schemes_data.items():
            throughput_data = data['throughput_data']
            if 'time' in throughput_data.columns and 'loss' in throughput_data.columns:
                plt.plot(throughput_data['time'], throughput_data['loss'], label=scheme)
        
        plt.xlabel('Time (s)')
        plt.ylabel('Loss Rate')
        plt.title(f'Loss Rate vs. Time - {profile}')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/{profile}_loss_time.png")
        plt.close()

def plot_delay_comparison(results, output_dir):
    """Generate bar plots comparing average and 95th percentile RTT."""
    for profile, schemes_data in results.items():
        avg_delays = []
        p95_delays = []
        scheme_names = []
        
        for scheme, data in schemes_data.items():
            avg_delays.append(data['avg_delay'])
            p95_delays.append(data['p95_delay'])
            scheme_names.append(scheme)
        
        # Create grouped bar chart
        x = np.arange(len(scheme_names))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x - width/2, avg_delays, width, label='Average RTT')
        ax.bar(x + width/2, p95_delays, width, label='95th Percentile RTT')
        
        ax.set_xlabel('Congestion Control Scheme')
        ax.set_ylabel('RTT (ms)')
        ax.set_title(f'RTT Comparison - {profile}')
        ax.set_xticks(x)
        ax.set_xticklabels(scheme_names)
        ax.legend()
        ax.grid(True, axis='y')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{profile}_rtt_comparison.png")
        plt.close()

def plot_throughput_vs_rtt(results, output_dir):
    """Generate throughput vs RTT scatter plot."""
    plt.figure(figsize=(10, 8))
    
    markers = ['o', 's', 'd', '^', 'v', '<', '>', 'p', '*']
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'orange', 'purple']
    
    points = []
    labels = []
    
    for profile, schemes_data in results.items():
        for i, (scheme, data) in enumerate(schemes_data.items()):
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            
            rtt = data['avg_delay']
            throughput = data['avg_throughput']
            
            plt.scatter(rtt, throughput, marker=marker, color=color, s=100, 
                       label=f"{scheme} ({profile})")
            
            points.append((rtt, throughput))
            labels.append(f"{scheme} ({profile})")
    
    # Invert x-axis as specified in the assignment
    plt.gca().invert_xaxis()
    
    plt.title('Throughput vs. RTT Comparison')
    plt.xlabel('RTT (ms) - Higher RTT closer to origin')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    
    # Add legend with unique entries
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='best')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/throughput_vs_rtt.png")
    plt.close()

def generate_comparison_table(results, output_dir):
    """Generate comparison tables in CSV format."""
    for profile, schemes_data in results.items():
        # Create a DataFrame for the comparison
        data = []
        for scheme, metrics in schemes_data.items():
            data.append({
                'Scheme': scheme,
                'Avg Throughput (Mbps)': metrics['avg_throughput'],
                'Avg RTT (ms)': metrics['avg_delay'],
                '95th Percentile RTT (ms)': metrics['p95_delay'],
                'Loss Rate (%)': metrics['loss_rate'] * 100
            })
        
        df = pd.DataFrame(data)
        
        # Save to CSV
        csv_file = f"{output_dir}/{profile}_comparison.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved comparison table to {csv_file}")
        
        # Also print to console
        print(f"\nComparison for {profile}:")
        print(df.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='Analyze Pantheon experiment results')
    parser.add_argument('--data-dir', default=os.path.expanduser('~/networks_assignment/data'),
                      help='Directory containing experimental data')
    parser.add_argument('--output-dir', default=os.path.expanduser('~/networks_assignment/graphs'),
                      help='Directory to save output graphs')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist
    
    # Parse experiment results
    results = parse_pantheon_logs(args.data_dir)
    
    if not results:
        print("No experiment results found. Make sure experiments have been run.")
        return 1
    
    # Generate plots
    plot_throughput_time_series(results, args.output_dir)
    plot_loss_time_series(results, args.output_dir)
    plot_delay_comparison(results, args.output_dir)
    plot_throughput_vs_rtt(results, args.output_dir)
    
    # Generate comparison tables
    generate_comparison_table(results, args.output_dir)
    
    print("\nAnalysis complete! Graphs saved to:", args.output_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
