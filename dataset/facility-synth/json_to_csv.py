#!/usr/bin/env python3
"""
Convert JSON file to CSV format.
This script handles the conversion of facility_v2_train.json to CSV format.
"""

import json
import csv
import sys
from pathlib import Path

def parse_facility_data(json_data):
    """
    Parse the facility data from the JSON file.
    
    Args:
        json_data: The loaded JSON data
        
    Returns:
        A list of dictionaries with input and answer fields
    """
    rows = []
    
    for item in json_data:
        # Extract the input text and answer
        input_text = item['fields']['input']
        answer = item['answer']  # Keep answer as a string, don't parse it
        
        # Create a row with just input and answer
        row = {
            'input': input_text,
            'answer': answer
        }
        
        rows.append(row)
        
    return rows

def convert_json_to_csv(input_file, output_file):
    """
    Convert a JSON file to CSV format.
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output CSV file
    """
    print(f"Converting {input_file} to {output_file}...")
    
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Parse the data
    rows = parse_facility_data(json_data)
    
    if not rows:
        print("No data found in the JSON file.")
        return
    
    # Define fieldnames explicitly to ensure consistent order
    fieldnames = ['input', 'answer']
    
    # Write to CSV with proper quoting
    with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(
            csvfile, 
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,  # Quote all fields for better compatibility
            quotechar='"',          # Use double quotes
            escapechar='\\'        # Use backslash as escape character
        )
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Conversion complete. Output saved to {output_file}")

def main():
    """Main function to handle command line arguments."""
    input_file = Path("/Users/justinai/Documents/Code/prompt-ops/ui-mockups/facility_v2_train.json")
    output_file = input_file.with_suffix('.csv')
    
    if not input_file.exists():
        print(f"Input file {input_file} does not exist.")
        sys.exit(1)
    
    convert_json_to_csv(input_file, output_file)

if __name__ == "__main__":
    main()
