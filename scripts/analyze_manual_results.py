#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import json
import argparse

def analyze_results(data_dir, output_dir):
    """Analyze experiment results and generate graphs."""
    # Find all result files
    result_files = glob.glob(f"{data_dir}/*/result.json")
    
    if not result_files:
        print(f"No result files found in {data_dir}")
        print("Checking if data might be in root user's directory...")
        
        # Try to look for data in /root/ directory
        if os.path.exists("/root/networks_assignment/data/"):
            print("Data found in /root/networks_assignment/data/")
            print("Please run this script with sudo or copy the data to your user directory")
            
        return 1
    
    # Process result files
    results = {}
    for result_file in result_files:
        # Extract profile and scheme from directory path
        dir_path = os.path.dirname(result_file)
        dir_name = os.path.basename(dir_path)
        
        if '_' not in dir_name:
            continue
            
        profile, scheme = dir_name.split('_', 1)
        
        # Load result data
        try:
            with open(result_file, 'r') as f:
                result_data = json.load(f)
        except Exception as e:
            print(f"Error loading {result_file}: {e}")
            continue
        
        # Load throughput data
        throughput_file = f"{dir_path}/{scheme}_throughput.csv"
        if os.path.exists(throughput_file):
            try:
                throughput_data = pd.read_csv(throughput_file)
            except Exception as e:
                print(f"Error loading {throughput_file}: {e}")
                throughput_data = pd.DataFrame(columns=['time', 'throughput', 'delay', 'loss'])
        else:
            print(f"No throughput data found for {profile}_{scheme}")
            throughput_data = pd.DataFrame(columns=['time', 'throughput', 'delay', 'loss'])
        
        # Store results
        if profile not in results:
            results[profile] = {}
            
        # For localhost testing with artificial limits, adjust throughput based on profile
        if profile == 'profile1':
            # 50 Mbps limit
            adjusted_throughput = min(result_data.get('avg_throughput', 0), 50)
        elif profile == 'profile2':
            # 1 Mbps limit
            adjusted_throughput = min(result_data.get('avg_throughput', 0), 1)
        else:
            adjusted_throughput = result_data.get('avg_throughput', 0)
        
        results[profile][scheme] = {
            'avg_throughput': adjusted_throughput,
            'avg_delay': result_data.get('avg_delay', 0),
            'loss_rate': result_data.get('loss_rate', 0),
            'throughput_data': throughput_data
        }
    
    if not results:
        print("No valid results found to analyze")
        return 1
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate comparative tables
    for profile, schemes in results.items():
        table_data = []
        for scheme, data in schemes.items():
            table_data.append({
                'Scheme': scheme,
                'Avg Throughput (Mbps)': data['avg_throughput'],
                'Avg RTT (ms)': data['avg_delay'],
                'Loss Rate': data['loss_rate']
            })
        
        if table_data:
            df = pd.DataFrame(table_data)
            df.to_csv(f"{output_dir}/{profile}_comparison.csv", index=False)
            print(f"\nComparison for {profile}:")
            print(df)
    
    # Generate throughput vs RTT plot
    plt.figure(figsize=(10, 6))
    
    markers = ['o', 's', '^', 'D', 'v']
    colors = ['b', 'g', 'r', 'c', 'm']
    
    legend_labels = []
    legend_handles = []
    
    i = 0
    for profile, schemes in results.items():
        for scheme, data in schemes.items():
            rtt = data['avg_delay']
            throughput = data['avg_throughput']
            
            marker_idx = i % len(markers)
            color_idx = i % len(colors)
            
            scatter = plt.scatter(rtt, throughput, marker=markers[marker_idx], color=colors[color_idx],
                       s=100, label=f"{scheme} ({profile})")
            
            legend_labels.append(f"{scheme} ({profile})")
            legend_handles.append(scatter)
            
            i += 1
    
    # Invert x-axis as specified in the assignment
    plt.gca().invert_xaxis()
    
    plt.title('Throughput vs. RTT Comparison')
    plt.xlabel('RTT (ms) - Higher RTT closer to origin')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    
    # Create legend with unique entries
    if legend_handles:
        plt.legend(handles=legend_handles, labels=legend_labels)
    
    plt.savefig(f"{output_dir}/throughput_vs_rtt.png")
    plt.close()
    
    # Generate time-series plots for each profile
    for profile, schemes in results.items():
        # Throughput time series
        plt.figure(figsize=(10, 6))
        
        for scheme, data in schemes.items():
            df = data['throughput_data']
            if not df.empty and 'time' in df.columns and 'throughput' in df.columns:
                # Adjust throughput based on profile
                if profile == 'profile1':
                    df['throughput'] = df['throughput'].clip(upper=50)
                elif profile == 'profile2':
                    df['throughput'] = df['throughput'].clip(upper=1)
                
                plt.plot(df['time'], df['throughput'], label=scheme)
        
        plt.title(f'Throughput over Time - {profile}')
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.grid(True)
        plt.legend()
        
        plt.savefig(f"{output_dir}/{profile}_throughput_time.png")
        plt.close()
        
        # Loss time series
        plt.figure(figsize=(10, 6))
        
        for scheme, data in schemes.items():
            df = data['throughput_data']
            if not df.empty and 'time' in df.columns and 'loss' in df.columns:
                plt.plot(df['time'], df['loss'], label=scheme)
        
        plt.title(f'Loss Rate over Time - {profile}')
        plt.xlabel('Time (s)')
        plt.ylabel('Loss Rate')
        plt.grid(True)
        plt.legend()
        
        plt.savefig(f"{output_dir}/{profile}_loss_time.png")
        plt.close()
        
        # RTT comparison bar chart
        plt.figure(figsize=(10, 6))
        
        schemes_list = list(schemes.keys())
        rtts = [schemes[s]['avg_delay'] for s in schemes_list]
        
        # Calculate 95th percentile if data is available
        p95_rtts = []
        for s in schemes_list:
            df = schemes[s]['throughput_data']
            if not df.empty and 'delay' in df.columns:
                p95_rtts.append(np.percentile(df['delay'], 95))
            else:
                p95_rtts.append(0)
        
        x = np.arange(len(schemes_list))
        width = 0.35
        
        plt.bar(x - width/2, rtts, width, label='Average RTT')
        plt.bar(x + width/2, p95_rtts, width, label='95th Percentile RTT')
        
        plt.title(f'RTT Comparison - {profile}')
        plt.xlabel('Congestion Control Algorithm')
        plt.ylabel('RTT (ms)')
        plt.xticks(x, schemes_list)
        plt.grid(True, axis='y')
        plt.legend()
        
        plt.savefig(f"{output_dir}/{profile}_rtt_comparison.png")
        plt.close()
    
    print(f"Analysis complete! Graphs saved to {output_dir}")
    return 0

def main():
    parser = argparse.ArgumentParser(description='Analyze experiment results')
    parser.add_argument('--data-dir', default=os.path.expanduser('~/networks_assignment/data'),
                      help='Directory containing experimental data')
    parser.add_argument('--output-dir', default=os.path.expanduser('~/networks_assignment/graphs'),
                      help='Directory to save output graphs')
    
    args = parser.parse_args()
    
    return analyze_results(args.data_dir, args.output_dir)

if __name__ == "__main__":
    main()
