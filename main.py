import argparse
import csv
import logging
import random
import sys
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.

    Returns:
        argparse.ArgumentParser: The argument parser object.
    """
    parser = argparse.ArgumentParser(description="Randomly permutes the format of data within a column while preserving its inherent characteristics.")
    parser.add_argument("csv_file", help="The CSV file to process.")
    parser.add_argument("column_name", help="The name of the column to permute.")
    parser.add_argument("-o", "--output_file", help="The output CSV file (default: <input_file>_masked.csv)", default=None)
    parser.add_argument("-l", "--locale", help="Faker locale (e.g., en_US, fr_FR). Defaults to en_US.", default="en_US")

    return parser

def permute_data_format(data, data_type, locale="en_US"):
    """
    Permutes the format of the given data based on its type.

    Args:
        data (str): The data to permute.
        data_type (str): The type of data (e.g., 'date', 'currency', 'telephone').
        locale (str): The Faker locale to use.

    Returns:
        str: The permuted data, or the original data if permutation fails.
    """
    fake = Faker(locale)
    try:
        if data_type == 'date':
            try:
                # Attempt to parse the date in multiple common formats.
                from dateutil import parser
                date_obj = parser.parse(data)
                return fake.date_time_this_decade().strftime('%Y-%m-%d') # Standard date format

            except ValueError:
                logging.warning(f"Could not parse date: {data}. Returning original value.")
                return data # Return the original data if parsing fails
        elif data_type == 'currency':
            amount = float(data.replace('$', '').replace(',', ''))  # Remove currency symbols and commas

            return f"${fake.random_number(digits=3)}.{fake.random_number(digits=2)}" # Basic currency format
        elif data_type == 'telephone':
            return fake.phone_number()
        else:
            logging.warning(f"Unknown data type: {data_type}. Returning random string.")
            return fake.pystr(min_chars=len(data), max_chars=len(data))
    except Exception as e:
        logging.error(f"Error permuting data: {e}. Returning original value.")
        return data  # Return original data on any error to prevent data loss

def detect_data_type(data):
    """
    Detects the type of data based on its format. This is a very basic implementation.

    Args:
        data (str): The data to analyze.

    Returns:
        str: The detected data type (e.g., 'date', 'currency', 'telephone', or 'unknown').
    """
    if isinstance(data, str):
        data = data.strip()
    if not isinstance(data, str) or not data:
        return 'unknown'  # Handle empty or non-string data
    
    # Basic date detection
    import re
    if re.match(r'\d{4}-\d{2}-\d{2}', data):
        return 'date'
    if re.match(r'\d{2}/\d{2}/\d{4}', data): #added basic date detection
        return 'date'
    if re.match(r'\$\d+(\,\d{3})*(\.\d{2})?', data):
        return 'currency'
    if re.match(r'(\+\d{1,3})?\s?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', data):
        return 'telephone' #Very basic phone number detection

    return 'unknown'

def main():
    """
    Main function to execute the data format permutation process.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    csv_file = args.csv_file
    column_name = args.column_name
    output_file = args.output_file or csv_file.replace(".csv", "_masked.csv") #Default output file name
    locale = args.locale

    try:
        with open(csv_file, 'r', newline='') as infile, \
                open(output_file, 'w', newline='') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            header = next(reader)  # Read the header row
            writer.writerow(header)  # Write the header row to the output file

            try:
                column_index = header.index(column_name)
            except ValueError:
                logging.error(f"Column '{column_name}' not found in the CSV file.")
                sys.exit(1)

            for row in reader:
                try:
                    original_data = row[column_index]
                    data_type = detect_data_type(original_data)
                    masked_data = permute_data_format(original_data, data_type, locale)
                    row[column_index] = masked_data
                    writer.writerow(row)
                except IndexError:
                    logging.warning(f"Row has fewer columns than expected. Skipping row.")
                    writer.writerow(row) # Still write the row to avoid shifting data unexpectedly
                except Exception as e:
                    logging.error(f"Error processing row: {e}. Writing original row.")
                    writer.writerow(row) # Write original row on error
        logging.info(f"Data masking completed. Output written to {output_file}")

    except FileNotFoundError:
        logging.error(f"File '{csv_file}' not found.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Usage Examples:

1.  Basic Usage:
    python main.py data.csv phone_numbers

    This will read the 'data.csv' file, permute the data in the 'phone_numbers' column,
    and save the masked data to 'data_masked.csv'. It will default to en_US locale.

2.  Specifying Output File:
    python main.py data.csv credit_cards -o masked_data.csv

    This is similar to the first example, but the output will be saved to 'masked_data.csv'.

3.  Specifying Locale:
    python main.py data.csv dates -l fr_FR

    This will use the French locale ('fr_FR') for generating masked data, which affects date formats
    and other locale-specific data.  If data.csv has dates, it will replace them with new,
    fake dates generated using the French locale.
"""