# Script to get an excel spreadsheet of all terms with a particular
# part of speech tag from a Toolbox dictionary.
# Python 3
import os
from sys import argv
import pandas as pd

# use this command line operation to type the script followed by part of speech tag
# to auto-generate an excel spreadsheet
script, pos = argv

# path to store auto-generated spreadsheets
path = "Output_files/"
if not os.path.exists(path):
    os.makedirs(path)
# path for dictionaries
dpath = "Dictionaries/"

dfile = dpath+"kha-Dictionary.txt" # the name of the dictionary file, in this case for Khasi (ISO 639-3: kha)
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

# open the files
tbfile = open(dfile, 'r')#, encoding="utf-8")
# store the name of the file
workfile = dfile[len(dpath):-4]
print(workfile)

num = 0
tbdict = {'word': {}, 'pos': {}, 'gloss': {}} # initialize a dict
headword = ""
current = ""
entry = {}
for line in tbfile:
    for k, v in markers.items():
        # check if the line starts with one of the markers
        if line.startswith(v):
            current = k# make the marker the current entry
            # if the current marker is the lexical entry
            if k == 'lx':
                # if the previous entry is not blank
                if headword != "":
                    # print(entry)
                    # check whether the entry contains the part of speech
                    if entry[headword]['ps'] == pos:
                        tbdict['word'][num] = entry[headword]['lx']
                        tbdict['pos'][num] = entry[headword]['ps']
                        tbdict['gloss'][num] = entry[headword]['ge']
                        # increment the counter
                        num += 1
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

# print(tbdict)

# convert the new tbdict to a dataframe
posdf = pd.DataFrame.from_dict(tbdict)
# print(posdf.columns)
# write the dataframe to a spreadsheet
xls_path = path+workfile+"_"+str(pos)+".xlsx"
posdf.to_excel(xls_path, index=False)
