"""
Script reads in Toolbox corpus file and makes replacements of tiers based on a
replacement table/dictionary. Does this iteratively for files in specified
directories.

Assumptions:
    - Corpus files are in TXT format and interlinearized, and file names begin
    with an ISO code followed by a dash, i.e.: kuf-Texts.txt
    - Replacement tables are in XLSX format, filenames begin with an ISO code
    followed by a dash, i.e.: kuf-Replacements.xlsx
    - Corpus files are in the 'corpath' folder
    - Replacement tables are in the 'dicpath' folder
    - New corpus files and logs are written to the 'wripath' folder

Possibly required adjustments:
    - line 109, 255, 304: adjust the list of tiers according to corpus file's format
    - line 412, 430: adjust according to the column names in replacement table
    
    Supported Toolbox tiers are \id, \ref \ELANBegin \ELANEnd, \ELANParticipant,
    \tx, \ph, \mb, \ge, \ps, \ft, \nt, \media
"""
import os, re, sys, shutil, string, logging, glob
import pandas as pd
from collections import OrderedDict
from chardet.universaldetector import UniversalDetector

# set the paths where files will be read/written
corpath = "Corpus_files/"# path for Toolbox corpus files
dicpath = "Dictionaries/"# path for Toolbox replacement dictionaries (in XLSX format)
wripath = "Output_files/"# path for new Toolbox corpus files

# # make the output directory if it doesn't exist
# if not os.path.exists(wripath):
#     os.makedirs(wripath)

# instantiate dict to save data of one utterance using a sorted dict because
# order is important; key is the fieldmarker, value the tier content
ref = OrderedDict()

"""
morpheme data gets saved in a special data structure for easy manipulation
[(word1, {"\\mb": [mb1, mb2]
          "\\ge": [ge1, ge2],
          "\\ps": [ps1, ps2]}),
 (word2, {...})]
"""
# instantiate regex to extract individual words from interlinearized Toolbox tiers
extract = re.compile(r"(\\\w+)\s*(.*)")
# instantiate list to save words
words = []

# define a logger function to store information about the process
def set_logger(activate=True, fname=wripath+"replace.log"):
    """Set up a logger.

    activate (bool): activates the logger
    fname: name of the log file
    """
    logger = logging.getLogger(__name__)

    if activate:
        logger.setLevel(logging.INFO)
        if fname is None:
            handler = logging.FileHandler("corpus_processer.log", mode="w", encoding='utf-8')
        else:
            handler = logging.FileHandler(fname, mode="w", encoding='utf-8')
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(funcName)s|%(levelname)s|%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    else:
        logger.disabled = True

    return logger

def add_tier(dictionary, line):
    """Extract label and data and add to a hash.

    dictionary (hash): some hash where data is added to
    line (str): tier
    """
    # extract field marker label and its data
    match = extract.match(line)
    label = match.group(1)
    data = match.group(2)
    # check if there are several defintions of the
    # same fieldmarker in one \ref
    if label in dictionary:
        # concatenate with hash content
        if label == "\\nt":
            dictionary[label] += " \n\\nt " + data
        else:
            dictionary[label] += " " + data
    else:
        # add to hash
        dictionary[label] = data

def has_errors(words=words, ref=ref):
    """Do various checks for the words and their morphemes."""
    # Check if there are words in the utterance at all
    if not words:
        return True

    # for logging purposes
    tref = ref["\\ref"]
    tierslist = ["\\tx", "\\mb", "\\ge", "\\ps", "\\lxid"]
    # check if morpheme tiers are missing or empty
    for field in tierslist:
        # check if morpheme tier occurs
        if field in ref:
            # check if morpheme field is empty
            if not ref[field]:
                logger.warning(
                    "{}|morpheme tiers empty".format(tref))
                return True
        else:
            logger.warning("{}|morpheme tiers missing".format(tref))
            print("{}|morpheme tiers missing".format(tref))
            return True

    # do checks for word and morpheme numbers
    for word, morphemes in words:
        # if number of words and morpheme groups do not match
        if len(morphemes) != len(tierslist)-1:#word == "" or
            logger.error("{}|word numbers don't match".format(tref))
            print("{}|word numbers don't match".format(tref))
            # print(word, morphemes)
            return True

        # if number of morphemes is not equal for all morpheme tiers
        # take number of \mb's as a random reference point
        n_units = len(morphemes["\\mb"])
        for tier in morphemes:
            if tier != "\\tx":
                if len(morphemes[tier]) != n_units:
                    logger.error("{}|morpheme numbers don't match".format(tref))
                    print("{}|morpheme numbers don't match".format(tref))
                    return True

    return False

def _add_words():
    """Extract and add words and intialize empty morpheme hash."""
    if "\\tx" in ref:
        # extract words splitting the processed line at whitespaces
        word_iterator = re.finditer(r"\S+", ref["\\tx"])

        # add every word to the list
        for word in word_iterator:
            words.append((word.group(), {}))
        # print(words, len(words))

def _add_morphemes():
    """Extract and add morphemes."""
    morpheme_tiers = {}
    if "\\ph" in tagslist:
        morpheme_tiers = {"\\mb", "\\ph", "\\ge", "\\ps", "\\lxid"}
    else:
        morpheme_tiers = {"\\mb", "\\ge", "\\ps", "\\lxid"}

    # go through every morpheme type tier
    for tier in morpheme_tiers:
        if tier not in ref:
            continue

        data = ref[tier]

        # get regex & iterator
        # for extracting morphemes per word (aka m-words)
        regex = re.compile(r"((\S+(\s+[=-]\s+|[=-]\s+))+(\S+(\s+[=-]|)+|\s+\S+)|\S+)")
        mwords_iterator = regex.finditer(data)

        # go over these m-words
        for i, mword in enumerate(mwords_iterator):
            # extract morphemes of this word splitting at whitespaces
            morphemes = re.split("\s+", mword.group())

            try:
                # add morphemes to the right word (via index)
                # to morpheme dictionary (at index 1)
                # under the right morpheme tier (\mb,\ge,\ps)
                words[i][1][tier] = morphemes

            # if there are less w-words than m-words
            except IndexError:
                # add it under an empty word
                words.append(("", {tier: morphemes}))

def build_words():
    """Build words and morphemes from tiers of an utterance."""
    words.clear()
    _add_words()
    _add_morphemes()

def iter_utterances(temp):
    """Iterate and yield all utterances."""
    org_file = temp

    # delete data of previous utterance (just as a precaution)
    ref.clear()

    # go through all data from a corpus file
    # and save data per utterance unter ref
    for line in org_file:

        # throw away the newline (and carriage return) at the end of a line
        line = line.rstrip("\r\n")

        # if new utterance starts
        if line.startswith("\\ref"):
            # yield data of previous utterance
            build_words()
            yield ref
            # delete data of previous utterance
            ref.clear()
            # add \ref to hash
            add_tier(ref, line)
            # print(line)

        # if any field marker starts
        elif line.startswith("\\"):
            add_tier(ref, line)
            # print(line)

        # if line does not start with \\, its data must belong
        # to the fieldmarker that directly comes before (except for \\id, which is handled in the writing phase)
        elif line:
            # get last added fieldmarker
            label = next(reversed(ref))
            # concatenate content
            ref[label] += " "+line

    # last utterance
    # build_words()

    yield ref

def write_file(temp, align=True, rebuild=True):
    """Write data of an utterance to the file.
    align (bool): whether the morphemes should be aligned
    rebuild (bool): whether words/morphemes should be rebuilt when aligning
    """
    new_file = temp

    # if words should be used and no errors were found in it
    if align and not has_errors():

        # check if words/morphemes should be rebuilt
        if rebuild:
            build_words()

        temptier = ("\\tx", "\\mb", "\\ge", "\\ps", "\\lxid")
        # build morpheme tiers directly in ref
        for tier in temptier:
            ref[tier] = ""
        # go through each word and its morpheme data
        for word, morphemes in words:

            # concatenate word to tier \tx
            ref["\\tx"] += word
            txlen = len(word.encode('utf-8'))

            # keep track of the longest unit group
            longest_group = 0
            # go through each slot in the word (e.g. via \mb)
            for i, _ in enumerate(morphemes["\\mb"]):

                # save the no. of chars for every unit in this slot
                lens = {}

                # keep track of the longest type of unit
                longest_unit = 0
                # go through every type of unit
                for unit in morphemes:

                    # concatenate unit i to tier of this unit type
                    ref[unit] += morphemes[unit][i]

                    # save no. of chars of this unit
                    lens[unit] = len(morphemes[unit][i].encode('utf-8'))#('utf-8'))#

                    # compare it to the longest unit seen so far
                    if longest_unit < lens[unit]:
                        longest_unit = lens[unit]
                    if longest_unit < txlen:
                        longest_unit = txlen

                # there is one whitespace between morphemes/words
                longest_unit += 1

                # add it to the unit group length
                longest_group += longest_unit

                # add necessary whitespaces between morphemes
                for unit in morphemes:
                    ref[unit] += (longest_unit - lens[unit])*" "
            # add necessary whitespaces between words
            ref["\\tx"] += (longest_group - txlen)*" "

    # Go through every possible tier in the right order
    for tier in ("\\ref", "\\sound", "\\ELANBegin", "\\ELANEnd",
                 "\\ELANParticipant", "\\tx", "\\mb", "\\ge",
                 "\\ps", "\\lxid", "\\ft", "\\nt", "\\media", "\\ELANMediaURL", "\\ELANMediaMIME", "\\id"):

        # write tier if it occurs in the ref
        if tier in ref:
            # check if it's the '\\id' tier
            if tier == "\\id":
                # if so, write its content to the file with a preceding newline
                new_file.write("\n"+tier + " " + ref[tier])#.rstrip())
            else:
                # if not, write its content to the file as-is
                new_file.write(tier + " " + ref[tier])#.rstrip())
            # new line after every tier
            new_file.write("\n")
    # insert empty line between utterances
    new_file.write("\n")

def update_utterance(words, pdict, lxid, ps, old, new):
    """Update words according to the replacement dictionary."""
    # check all words for matches in replacement dict
    for word, morphemes in words:
        # twd = word.lower()
        # print(word, morphemes)
        if ps == "\\tx":
            for num, item in enumerate(morphemes["\\mb"]):
                twd = morphemes[lxid][num].lower()
                if twd in pdict.keys():
                    ref[ps] = ref[ps].replace(pdict[twd][old], pdict[twd][new])
                    logger.info("changed form '{}' tier \{} '{}' to '{}' in {}".format(
                        twd, ps, pdict[twd][old], pdict[twd][new], ref["\\ref"]))
        else:
            for num, item in enumerate(morphemes[ps]):
                twd = morphemes[lxid][num].lower()
                if twd in pdict.keys():
                    # print(twd, words)
                    if item == pdict[twd][old]:
                        morphemes[ps][num] = morphemes[ps][num].replace(pdict[twd][old], pdict[twd][new])
                        logger.info("changed form '{}' tier \{} '{}' to '{}' in {}".format(
                            twd, ps, pdict[twd][old], pdict[twd][new], ref["\\ref"]))

def get_repdict(dicfile, lex, old, new):
    tdf = pd.read_excel(dicfile)
    if lex == 'lxid':
        tdf[lex] = tdf[lex].astype(str)
        tdf[lex] = tdf[lex].apply(lambda x: x.zfill(4))
    tdf = tdf[[lex, old, new]]
    trange = list(range(len(tdf)))
    tempdict = tdf.to_dict()
    pdict = {}

    for num in trange:
        if tempdict[lex][num] not in pdict.keys():
            pdict[tempdict[lex][num]] = {old: tempdict[old][num], new: tempdict[new][num]}
        else:
            pass

    return pdict

corpfiles = []
for fn in glob.glob(corpath+"*.txt"):
    corpfiles.append(fn)

dictfiles = []
for fn in glob.glob(dicpath+"*.xlsx"):
    dictfiles.append(fn)

for tbpath in corpfiles:
    tagslist = []
    tbiso = tbpath[len(corpath):].split("-")[0]
    # get the complete list of tiers in the dataset file
    xfile = open(tbpath, "r")#, encoding=encoding)#"utf-8")#"utf-8")
    for zline in xfile:
        templine = re.split("\s+", zline)
        if '\\' in templine[0]:
            if templine[0] not in tagslist:
                tagslist.append(templine[0])
    print(tagslist)

    for dicfile in dictfiles:
        diciso = dicfile[len(dicpath):].split("-")[0]
        if tbiso == diciso:
            tbwpath = wripath+tbpath[len(corpath):]

            # detects encoding
            detector = UniversalDetector()
            # reuse the detector by a reset
            detector.reset()

            # read (some) lines in binary mode to detect encoding
            with open(tbpath, "rb") as f:
                for line in f:
                    detector.feed(line)
                    if detector.done:
                        break

            detector.close()

            # guessed encoding
            encoding = detector.result["encoding"]

            tfile = open(tbpath, "r")#, encoding=encoding)#"utf-8")#
            tbwrite = open(tbwpath, "w", encoding="utf-8")#"utf-8")

            logger = set_logger()
            # the following function gets the replacement columns from the excel spreadsheet
            # first argument is the spreadsheet file, second is the column to use as reference,
            # third is the column of forms to replace, fourth is the column of replacements
            pdict = get_repdict(dicfile, 'lxid', 'old_ps', 'new_ps')

            # go through each utterance of all corpus files
            for utterance in iter_utterances(tfile):
                # only process ref's (not \_sh for example)
                if "\\ref" in utterance:
                    # rebuild words/morphemes
                    build_words()

                # if there are no errors in the morpheme data
                if not has_errors():
                    # change data if necessary
                    # first argument is the dictionary of forms in the utterance,
                    # second is the dictionary of replacements, third is the field to check
                    # for identifying replacement items, fourth is the field to replace,
                    # fifth is the column in the replacement dictionary with the form to replace,
                    # sixth is the column in the replacement dictionary with the replacement form
                    try:
                        update_utterance(words, pdict, "\\lxid", "\\ps", 'old_ps', 'new_ps')
                    except:
                        print(ref["\\ref"])

                # write (un)changed utterance back to file
                write_file(tbwrite, rebuild=False)
