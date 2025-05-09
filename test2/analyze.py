#!/usr/bin/env python3
import re
import argparse
import pandas as pd
import numpy as np
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def parse_log_file(file_path):
    """Parse log file to extract File Interfaces and end-to-end test latency data"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract File Interfaces data
    file_interfaces_pattern = r'Type,Size,Cycles\n(.*?)(?=E2E Test|$)'
    file_interfaces_match = re.search(file_interfaces_pattern, content, re.DOTALL)
    
    file_interfaces_data = []
    if file_interfaces_match:
        lines = file_interfaces_match.group(1).strip().split('\n')
        for line in lines:
            parts = line.split(',')
            if len(parts) == 3:
                op_type, size, cycles = parts
                # Exclude abnormal values (overflow values)
                if not int(cycles) > 1e10:
                    try:
                        file_interfaces_data.append({
                            'Type': op_type,
                            'Size': int(size),
                            'Cycles': int(cycles)
                        })
                    except ValueError:
                        # Skip lines that can't be converted to integers
                        continue
    
    # Extract end-to-end test data
    e2e_data = []
    # Find data blocks after E2E Test
    e2e_section_match = re.search(r'E2E Test\n(.*?)$', content, re.DOTALL)
    if e2e_section_match:
        e2e_section = e2e_section_match.group(1)
        # Find all Size,Cycles blocks
        size_cycles_blocks = re.finditer(r'Size,Cycles\n(.*?)(?=Size,Cycles|$)', e2e_section, re.DOTALL)
        for block_match in size_cycles_blocks:
            block = block_match.group(1).strip()
            lines = block.split('\n')
            for line in lines:
                parts = line.split(',')
                if len(parts) == 2:
                    size, cycles = parts
                    # Exclude abnormal values
                    if not int(cycles) > 1e10:
                        try:
                            e2e_data.append({
                                'Size': int(size),
                                'Cycles': int(cycles)
                            })
                        except ValueError:
                            # Skip lines that can't be converted to integers
                            continue
    
    return file_interfaces_data, e2e_data

# Remove outlier because of fluctuation.
def remove_outliers(df, n=3):
    def filter_group(group):
        mean = group['Cycles'].mean()
        std = group['Cycles'].std()
        return group[(group['Cycles'] >= mean - n * std) & (group['Cycles'] <= mean + n * std)]
    return df.groupby('Type', group_keys=False).apply(filter_group)

def analyze_and_compare(base_file, test_file):
    """Analyze and compare performance data from two log files"""
    base_file_interfaces, base_e2e = parse_log_file(base_file)
    test_file_interfaces, test_e2e = parse_log_file(test_file)
    
    # Convert to DataFrames for analysis
    base_file_df = pd.DataFrame(base_file_interfaces)
    test_file_df = pd.DataFrame(test_file_interfaces)
    base_e2e_df = pd.DataFrame(base_e2e)
    test_e2e_df = pd.DataFrame(test_e2e)
    
    # Apply outlier removal to File Interfaces data
    if not base_file_df.empty and 'Type' in base_file_df.columns:
        base_file_df = remove_outliers(base_file_df)
    if not test_file_df.empty and 'Type' in test_file_df.columns:
        test_file_df = remove_outliers(test_file_df)
    
    # Check if DataFrames are empty or missing necessary columns
    if base_e2e_df.empty or test_e2e_df.empty:
        print("WARNING: No end-to-end test data in one or both log files")
        all_e2e_sizes = []
    else:
        if 'Size' not in base_e2e_df.columns or 'Size' not in test_e2e_df.columns:
            print("WARNING: Size column missing in end-to-end test data")
            all_e2e_sizes = []
        else:
            all_e2e_sizes = sorted(set(base_e2e_df['Size'].unique()) | set(test_e2e_df['Size'].unique()))
    
    if base_file_df.empty or test_file_df.empty:
        print("WARNING: No File Interfaces data in one or both log files")
        all_file_sizes = []
    else:
        if 'Size' not in base_file_df.columns or 'Size' not in test_file_df.columns:
            print("WARNING: Size column missing in File Interfaces data")
            all_file_sizes = []
        else:
            all_file_sizes = sorted(set(base_file_df['Size'].unique()) | set(test_file_df['Size'].unique()))
    
    # Compare end-to-end test results
    print("=== End-to-End Performance Comparison ===")
    if not all_e2e_sizes:
        print("No comparable end-to-end test data")
    else:
        for size in all_e2e_sizes:
            base_size_data = base_e2e_df[base_e2e_df['Size'] == size]['Cycles'] if 'Size' in base_e2e_df.columns else pd.Series()
            test_size_data = test_e2e_df[test_e2e_df['Size'] == size]['Cycles'] if 'Size' in test_e2e_df.columns else pd.Series()
            
            if not base_size_data.empty and not test_size_data.empty:
                # Remove outliers for E2E data
                base_size_df = base_e2e_df[base_e2e_df['Size'] == size].copy()
                test_size_df = test_e2e_df[test_e2e_df['Size'] == size].copy()
                
                # Add a dummy 'Type' column for outlier removal
                base_size_df['Type'] = 'E2E'
                test_size_df['Type'] = 'E2E'
                
                base_size_df = remove_outliers(base_size_df)
                test_size_df = remove_outliers(test_size_df)
                
                base_mean = base_size_df['Cycles'].mean()
                test_mean = test_size_df['Cycles'].mean()
                diff = test_mean - base_mean
                diff_percent = (diff / base_mean) * 100 if base_mean != 0 else float('inf')
                
                print(f"\n--- Average End-to-End Cycles ({size} bytes) ---")
                print(f"{'Base Mean(E2E)':<15} {'Test Mean(E2E)':<15} {'Diff(E2E)':<15} {'Diff %':<10}")
                print(f"{base_mean:<15.6e} {test_mean:<15.6e} {diff:<15.6e} {diff_percent:<10.6f}")
            else:
                print(f"\n--- Average End-to-End Cycles ({size} bytes) ---")
                if base_size_data.empty:
                    print(f"No base data for size {size}")
                if test_size_data.empty:
                    print(f"No test data for size {size}")
    
    # Compare File Interfaces results
    print("\n=== File Interfaces Performance Comparison ===")
    if not all_file_sizes:
        print("No comparable File Interfaces data")
    else:
        for size in all_file_sizes:
            base_size_data = base_file_df[base_file_df['Size'] == size] if 'Size' in base_file_df.columns else pd.DataFrame()
            test_size_data = test_file_df[test_file_df['Size'] == size] if 'Size' in test_file_df.columns else pd.DataFrame()
            
            if not base_size_data.empty and not test_size_data.empty:
                print(f"\n--- Average Operation Cycles ({size} bytes) ---")
                print(f"{'Type':<15} {'Base Mean(O2O)':<15} {'Test Mean(O2O)':<15} {'Diff(O2O)':<15} {'Diff %':<10}")
                
                # Get all operation types
                all_types = sorted(set(base_size_data['Type'].unique()) | set(test_size_data['Type'].unique()))
                
                for op_type in all_types:
                    base_type_data = base_size_data[base_size_data['Type'] == op_type]['Cycles'] if 'Type' in base_size_data.columns else pd.Series()
                    test_type_data = test_size_data[test_size_data['Type'] == op_type]['Cycles'] if 'Type' in test_size_data.columns else pd.Series()
                    
                    if not base_type_data.empty and not test_type_data.empty:
                        base_mean = base_type_data.mean()
                        test_mean = test_type_data.mean()
                        diff = test_mean - base_mean
                        diff_percent = (diff / base_mean) * 100 if base_mean != 0 else float('inf')
                        
                        print(f"{op_type:<15} {base_mean:<15.6e} {test_mean:<15.6e} {diff:<15.6e} {diff_percent:<10.6f}")
                    else:
                        if base_type_data.empty:
                            print(f"{op_type:<15} No base data")
                        if test_type_data.empty:
                            print(f"{op_type:<15} No test data")
            else:
                print(f"\n--- Average Operation Cycles ({size} bytes) ---")
                print("Insufficient data for comparison")

def main():
    parser = argparse.ArgumentParser(description='Analyze and compare UEFI performance logs')
    parser.add_argument('--base', required=True, help='Path to baseline log file')
    parser.add_argument('--test', required=True, help='Path to test log file')
    
    args = parser.parse_args()
    
    try:
        analyze_and_compare(args.base, args.test)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
