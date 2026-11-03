import csv


def read_bills_from_file(file_name):
    rows = []
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for reader_row in reader:
            reader_row[0] = reader_row[0].strip().lower()
            reader_row[1] = int(reader_row[1])
            reader_row[2] = int(reader_row[2])
            reader_row[3] = float(reader_row[3])
            rows.append(reader_row)
    return rows


def read_bonds_from_file(file_name):
    rows = []
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for reader_row in reader:
            reader_row[0] = reader_row[0].strip().lower()
            reader_row[1] = float(reader_row[1])
            reader_row[2] = int(reader_row[2])
            reader_row[3] = int(reader_row[3])
            reader_row[4] = int(reader_row[4])
            rows.append(reader_row)
    return rows
