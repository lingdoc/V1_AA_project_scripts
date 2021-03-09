# Script for replacing items in a Toolbox dictionary based on a spreadsheet
# of lexical items and replacement forms.
# Python 3
import os
import pandas as pd
import numpy as np
from collections import OrderedDict, defaultdict

"""
A function that checks whether the items should be replaced.
  Arguments are:
    'entry': the dict that stores lexical entry content from the Toolbox dictionary
    'headword': the lexeme of the current entry
    'readict': the dict of forms from the replacement table
    'reprange': an enumerated list of numbers referring to the replacement table forms
    'lx': the Toolbox marker that identifies the main lexical item in a given entry
    'ps': the Toolbox marker that should be replaced in a given entry
    'old': the column heading in the replacement spreadsheet that identifies the old term
    'new': the column heading in the replacement spreadsheet that identifies the old term
"""
def check_replace(entry, headword, readict, reprange, lx, ps, old, new):
    for num in reprange:
        if headword == readict[lx][num]:
            if entry[headword][ps] == readict[old][num]:
                entry[headword][ps] = readict[new][num]
        else:
            pass

    return entry[headword][ps]

"""
A function that writes each entry's item to a file.
  Arguments are:
    'filewrite': the file to be written
    'pre': the Toolbox marker of a term in an entry
    'entry': the Python dict that stores an entry
    'ln': the key for accessing a particular entry in the Python dict
    'temptext': the line break character used
"""
def write_entry(filewrite, headword, pre, entry, ln, temptext):
    try:
        filewrite.write(pre+entry[headword][ln]+temptext)
    except:
        pass

# path to store auto-generated spreadsheets
path = "Output_files/"
if not os.path.exists(path):
    os.makedirs(path)
# path for dictionaries
dpath = "Dictionaries/"
# the location/name of the replacement table file
repfile = dpath+'kha-replacetable.xlsx'
# the location/name of the Toolbox dictionary file to be replaced
dfile = dpath+'kha-Dictionary.txt'
# open the Toolbox dictionary
tbfile = open(dfile, 'r')
# store the name of the file
workfile = dfile[len(dpath):-4]
# create a new text file to write the new entries in the toolbox format, using
# the Toolbox dictionary filename as a basis for the new file
newfile = workfile+"_NEW.txt"
filewrite = open(path+newfile, "w")#, encoding='utf-8')
# open the excel spreadsheet file
reader = pd.read_excel(repfile)
reader = reader[['lx', 'Old pos', 'New pos']]# these are the column headers with lexeme and replacement information
# convert the spreadsheet file to a python dictionary ordered by row number
readict = reader.to_dict()
reprange = list(range(len(reader)))

# below are Toolbox codes for the lines, edit for different dictionary formats
idtext = "\\_sh v3.0  231  MDF 4.0" # this is the header for Toolbox dictionaries
temptext = "\n" # use this variable as a placeholder
# these are the field markers in a given Toolbox dictionary entry
markers = {'lx': "\\lx ", 'alt': "\\a ", 'hm': "\\hm ", 'ph': "\\ph ", 'ps': "\\ps ",
            'ge': "\\ge ", 'nt': "\\nt ", 'dt': "\\dt "}
# print out the markers in the original Toolbox dictionary file to ensure that it has the same markers
with open(dfile, 'r') as tbtemp:
    markerlist = []
    for lt in tbtemp:
        if lt.startswith("\\"):
            tpline = lt.split()[0]
            if tpline not in markerlist:
                markerlist.append(tpline)
    print(markerlist)
    tbtemp.close()
input("Check field markers and press any key to continue")

entry = {}# the dict for storing entries
headword = ''# the headword for the entry
current = ''# the current marker in the entry
filewrite.write(idtext+temptext+temptext)# write the header to the new file
# go through each line in the dictionary file
for line in tbfile:
    for k, v in markers.items():
        # check if the line starts with one of the markers
        if line.startswith(v):
            current = k# make the marker the current entry
            # if the current marker is the lexical entry
            if k == 'lx':
                # if the previous entry is not blank
                if headword != "":
                    # run the function to replace the element from the replacement table
                    check_replace(entry, headword, readict, reprange, 'lx', 'ps', 'Old pos', 'New pos')
                    # then write the new entry to the new file
                    for key, val in markers.items():
                        write_entry(filewrite, headword, val, entry, key, temptext)
                    filewrite.write(temptext)
                # reset the entry dict with the current lexical item as headword/key
                entry = {}
                headword = line[len(v):].rstrip()# get the line
                entry[headword] = {k: headword}# build a mini-dict
            # if the current marker is not the lexeme but one of the others
            else:
                # get the entry
                tword = line[len(v):].rstrip()
                # add it to the dict or append to existing dict entry
                if k in entry[headword].keys():
                    entry[headword][k] += "\n"+v+tword
                else:
                    entry[headword][k] = tword

# write the last entry of the dictionary
for k, v in markers.items():
    write_entry(filewrite, headword, v, entry, k, temptext)
