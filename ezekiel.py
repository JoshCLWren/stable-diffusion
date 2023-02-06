"""
script to format the book of ezekiel csv into a txt file
"""

import csv
import re

def main():
    """main function"""
    with open('/Users/joshwren/Code/playground/ml_stuff/bible/ezekiel.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        with open('ezekiel.txt', 'w') as txt_file:
            for line in csv_reader:
                txt_file.write(line[-1] + '\n')

if __name__ == '__main__':
    main()