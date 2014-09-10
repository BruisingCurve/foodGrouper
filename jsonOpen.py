#!/usr/bin/env python
"""
jsonOpen.py
author p.phelps
Open series json file
"""

import json
import pandas as pd
from pprint import pprint
import pdb

def jsonOpen(filepath):
    '''
    jsonOpen(filepath) - Call this on a filepath string to open your json file.
        opening is done line-by-line
        Returns - Concatinated pandas dataframe from the json file
    '''
    with open(filepath) as f:
        for line in f:
            data = pd.DataFrame(json.loads(line) for line in f)
    return data

def main():
    data = jsonOpen()
    pprint(data)
    pdb.set_trace()

if __name__ == '__main__':
	main()