import csv
import os

def get_data_from_csv(csv_file_name):
	data = []

	file_path = 'csvs' + os.path.sep + csv_file_name + '.csv'

	with open(file_path, encoding="UTF-8-SIG") as csv_file:
		csv_dictionary = csv.DictReader(csv_file, delimiter=',')

		for dictionary_row in csv_dictionary:
			if 'Title' not in dictionary_row and 'Make' in dictionary_row and 'Model' in dictionary_row and 'Year' in dictionary_row:
				dictionary_row['Title'] = f"{dictionary_row['Year']} {dictionary_row['Make']} {dictionary_row['Model']}"
			data.append(dictionary_row)

	return data
