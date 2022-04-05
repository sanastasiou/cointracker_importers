import argparse
import csv
from importlib.metadata import metadata
import os
import re
import datetime
from xmlrpc.client import boolean

class NexoTupleEnum:
    Date = 0
    Type = 1
    SentCurrency = 2
    SentQuantity = 3
    ReceivedCurrency = 4
    ReceivedQuantity = 5
    USDEquivalent = 6

def parse_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@', description = "Script which modifies nexo csv file for consumption by cointracker.")
    parser.add_argument('--nexo', required = True, metavar = 'FILENAME', help ="Nexo csv file to modify")
    parser.add_argument("--out", type=str, required = False, metavar = 'FILENAME', help = "Filepath for output file. If ommited, output file is created in the same directory as input file.")
    parser.add_argument("--mined", type=boolean, required=False, help = "Treat all deposits as mined income.")
    args = parser.parse_args()
    return args

def convert_date_time(date):
    return f"{date.month:02d}/{date.day:02d}/{date.year} {date.hour:02d}:{date.minute:02d}:{date.second:02d}"

def convert_to_valid_currency(currency):
    if currency == 'NEXONEXO':
        return 'NEXO'
    elif currency == 'USDTERC':
        return 'USDT'
    else:
        return currency

def convert(args):
    file = args.nexo
    output_filepath = args.out
    with open(file, 'r') as input_file:
        nexo_reader   = csv.DictReader(input_file, delimiter=',')
        reader_tuple = []
        date_regex = re.compile(r"(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)")
        for row in nexo_reader:
            reader_tuple.append((
                datetime.datetime(
                    year=int(date_regex.search(row['Date / Time']).group(1)),
                    month=int(date_regex.search(row['Date / Time']).group(2)),
                    day=int(date_regex.search(row['Date / Time']).group(3)),
                    hour=int(date_regex.search(row['Date / Time']).group(4)),
                    minute=int(date_regex.search(row['Date / Time']).group(5)),
                    second=int(date_regex.search(row['Date / Time']).group(6))),
                row['Type'],
                row['Input Currency'],
                row['Input Amount'],
                row['Output Currency'],
                row['Output Amount'],
                row['USD Equivalent'])
            )
        sorted_tuple = sorted(reader_tuple, key=lambda tup: tup[0])
        output_file = output_filepath
        if output_filepath is None:
            output_file = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0] + '_cointracker.csv')

            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = ['Date', 'Received Quantity', 'Received Currency', 'Sent Quantity', 'Sent Currency', 'Fee Amount', 'Fee Currency', 'Tag']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in sorted_tuple:
                    if (row[NexoTupleEnum.Type] == 'Interest' or row[NexoTupleEnum.Type] == 'FixedTermInterest') and float(row[NexoTupleEnum.ReceivedQuantity]) > 0.0: #Do not import loan interest to cointracker
                        writer.writerow({'Date':  convert_date_time(row[NexoTupleEnum.Date]), 'Received Quantity': row[NexoTupleEnum.ReceivedQuantity], 'Received Currency': convert_to_valid_currency(row[NexoTupleEnum.ReceivedCurrency]), 'Sent Quantity': '', 'Sent Currency': '', 'Fee Amount': '', 'Fee Currency': '', 'Tag': 'staked'})
                    elif row[NexoTupleEnum.Type] == 'Exchange':
                        pair    = row[NexoTupleEnum.SentCurrency].strip().split("/")
                        amounts = []
                        amounts.append(f'<replace with actual amount of {convert_to_valid_currency(pair[0].strip())} for this transaction>')
                        amounts.append(row[NexoTupleEnum.ReceivedQuantity])
                        writer.writerow({'Date': convert_date_time(row[NexoTupleEnum.Date]), 'Received Quantity': amounts[1].strip(), 'Received Currency': convert_to_valid_currency(pair[1].strip()), 'Sent Quantity': amounts[0], 'Sent Currency': convert_to_valid_currency(pair[0].strip()), 'Fee Amount': '', 'Fee Currency': '', 'Tag': ''})
                    elif row[NexoTupleEnum.Type] == 'Deposit':
                        writer.writerow({'Date': convert_date_time(row[NexoTupleEnum.Date]), 'Received Quantity': row[NexoTupleEnum.ReceivedQuantity], 'Received Currency': convert_to_valid_currency(row[NexoTupleEnum.ReceivedCurrency]), 'Sent Quantity': '', 'Sent Currency': '', 'Fee Amount': '', 'Fee Currency': '', 'Tag': 'mined' if args.mined else ''})
                    elif row[NexoTupleEnum.Type] == 'Withdrawal':
                        writer.writerow({'Date': convert_date_time(row[NexoTupleEnum.Date]), 'Received Quantity': '', 'Received Currency': '', 'Sent Quantity': row[NexoTupleEnum.SentQuantity][1:], 'Sent Currency': convert_to_valid_currency(row[NexoTupleEnum.SentCurrency]), 'Fee Amount': 0, 'Fee Currency': convert_to_valid_currency(row[NexoTupleEnum.SentCurrency]), 'Tag': ''})
                    else:
                        continue
            print(f"Cointracker compatible file written to: {output_file}.")
    return

def main():
    args = parse_args()
    print(f"Modifying file: {args.nexo} to cointracker format...")
    convert(args)
    return 0

if __name__ == "__main__":
    res = main()
    exit(res)