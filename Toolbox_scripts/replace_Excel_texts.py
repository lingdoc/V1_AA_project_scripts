"""
Script reads in an annotated Excel spreadsheet file and makes replacements of items
in tiers based on a replacement table/dictionary. Does this iteratively for files
in specified directories.

Assumptions:
    - Corpus files are in XLSX format and interlinearized, and file names begin
    with an ISO code followed by a dash, i.e.: kha-Nagaraja.xlsx
    - Replacement tables are in XLSX format, filenames begin with an ISO code
    followed by a dash, i.e.: kha-Reptable.xlsx
    - Corpus files are in the 'corpath' folder
    - Replacement tables are in the 'dicpath' folder
    - New corpus files and logs are written to the 'wripath' folder

    Tiers for replacement are currently specified manually, with 'lx' entries in
    the replacement tables corresponding to 'IPA:' tiers in the annotated
    spreadsheets, and 'Old pos' and 'New pos' in the replacement tables
    corresponding to the 'pos:' tiers in the spreadsheets.
"""
import sys, os, glob, re
import pandas as pd
import numpy as np
from pandas import ExcelWriter
from tqdm import tqdm

tablespath = "Dictionaries/" # path for the replacement tables
repath = "Corpus_files/" # path containing annotated spreadsheets
wripath = "Output_files/"# path for new Toolbox corpus files
# make the new corpus directory if it doesn't exist
if not os.path.exists(wripath):
    os.makedirs(wripath)
# use this regex to split on morpheme boundaries = (clitic) and - (affix)
free = r"(=|-)"

# define a function to replace items in entries based on the replacement table
def replace_entries(repdict, reprange, repldict, nums, wds, pos, ipa, gl, free):
    # iterate through the replacement dictionary
    for rep in reprange:
        # below are the columns accessed by row number
        lx = repldict['lx'][rep] # lexical entry
        # ph = repldict['ph'][rep] # phonetic entry
        ps = repldict['Old pos'][rep] # old part of speech
        # ge = repldict['ge'][rep] # old gloss
        rps = repldict['New pos'][rep] # new part of speech
        # attempt to replace the corresponding entries
        try:
            # check if the item at this location is in the replacement dictionary
            if wds == lx:
                # check if the part of speech at this location is the same
                if repdict[pos][nums] == ps:
                    if rps != '':
                        # if so, replace it in the stored entries dictionary
                        repdict[pos][nums] = rps
            # otherwise check if the item contains the lexical entry
            elif lx in wds:
                # check if the part of speech is present
                if ps in repdict[pos][nums]:
                    # if so, split the repdict entry using regex, retaining the proclitic/prefix marker
                    cell = repdict[pos][nums]
                    cellist = list(filter(None, re.split(free, cell)))
                    for nx, x in enumerate(cellist):
                        # check if any of the list elements are the same as the 'ph' col in our replacement dictionary entry
                        if ps == x:
                            # print(cellist, nx, x)
                            if rps != '':
                                cellist[nx] = cellist[nx].replace(ps, rps) # replace the list element with the replacement entry
                                repdict[pos][nums] = "".join(cellist) # join the list and replace the df.loc cell with this new one
        except:
            pass

# define a function to iterate through the spreadsheets and their entries
def iterate_entries(tempdict, reprange, repldict, head, free):
    headers = [] # list to store the different headers for lines in the spreadsheet
    repdict = {} # dictionary to store each interlinearized sentence
    newdict = {} # dictionary to store the changed entries
    # iterate through the dictionary made from the spreadsheet
    for key, val in tempdict.items():
        headers.append(val[0])# store the header info
        # if the header is blank, this is the end of an entry
        if val[0] is np.nan:
            repdict[key] = val # store the line in the replacement dict
            # iterate through the entries in the replacement dict
            for k, v in repdict.items():
                # if the header corresponds to 'IPA:' then this is the line we check for lexical items
                if v[0] == head:
                    # look at each subentry in this line
                    for nums, wds in v.items():
                        replace_entries(repdict, reprange, repldict, nums, wds, pos, ipa, gl, free)
                # store the changed entry in the new dict
                newdict[k] = v
            # reset the replacement entry to blank
            repdict = {}
        # if the header is not blank
        else:
            # store the line in the replacement entry dictionary
            repdict[key] = val
            if val[0][:-1] == 'IPA':
                ipa = key # set the line number for the IPA line
            elif val[0][:-1] == 'gloss':
                gl = key # set the line number for the gloss line
            elif val[0][:-1] == 'pos':
                pos = key # set the line number for the part of speech line

            # check if this is the last line in the spreadsheet
            if key == len(tempdict)-1:
                # store the last entry
                for k, v in repdict.items():
                    # if the header corresponds to 'IPA:' then this is the line we check for lexical items
                    if v[0] == head:
                        # look at each subentry in this line
                        for nums, wds in v.items():
                            replace_entries(repdict, reprange, repldict, nums, wds, pos, ipa, gl, free)
                    # store the changed entry in the new dict
                    newdict[k] = v
    # print(len(tempdict))
    headers = list(set(headers))
    print(headers)
    newdf = pd.DataFrame.from_dict(newdict, orient='index')
    print(newdf.head())
    newdf.to_excel(wripath+testpath[repathlen:-5]+"_replaced.xlsx", index=False, header=False)

# store filenames of excel format replacement tables
filenames = []
for filen in glob.glob(tablespath+"*.xlsx"):
    filenames.append(filen)

# store filenames of excel format annotated spreadsheets
testfiles = []
for filen in glob.glob(repath+"*.xlsx"):
    testfiles.append(filen)

repathlen = len(repath) # the length of the path used when creating new files

# open each replacement table
for filen in filenames:
    repiso = filen[len(tablespath):len(tablespath)+3]
    repset = pd.read_excel(filen) # read the table into a dataframe
    reprange = list(range(len(repset))) # get a list of the row numbers
    repldict = repset.to_dict() # transform the dataframe into a dict for quicker access
    # open each of the annotated spreadsheets and tqdm it to give a progress bar
    for testpath in tqdm(testfiles):
        tempiso = testpath[repathlen:repathlen+3]
        if tempiso == repiso:
            testdf = pd.read_excel(testpath, header=None) # read the spreadsheet as a dataframe
            testlen = len(testdf) # check the length of the spreadsheet
            # print(testdf.head()) # check the spreadsheet
            # print(testlen) # print how many lines it has
            tempdict = testdf.to_dict(orient='index') # convert the spreadsheet to an embedded dict with index as keys
            # print(tempdict.keys())
            # print(len(tempdict)) # check the length of the dict to ensure it is the same as the spreadsheet
            iterate_entries(tempdict, reprange, repldict, "IPA:", free)
