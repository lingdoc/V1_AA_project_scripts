# Scripts for Toolbox and annotations

Contributors: Hiram Ring, Wei Wei Lee

The aim of these scripts are to assist in manipulating and editing annotation files in the **V1 project @ UZH**, based on interlinearization of language data using [Toolbox](https://software.sil.org/toolbox/), our annotation tool of choice, not least because it works directly with TXT files. The following scripts are included in this directory:

- `check-terms.py` outputs an excel spreadsheet for each part of speech represented in a Toolbox dictionary, which allows for the creation of replacement tables.

- `dict_replace.py` (old version) replaces items in a Toolbox dictionary based on their lexical form as indicated in a replacement table. Currently only replaces part of speech and assumes a particular format of the replacement table.

- `dict_replace_new.py` (new version) has the same function as the old version, but replaces items based on their lexical ID and current value on the tier you want to change. Can replace \lx, \ps, \ge, and probably other tiers, but those have not been tested yet.
	- note: be careful if you have a large amount of text on one of the tiers, it may be cut off.


- `replace_Toolbox_texts.py` (old version) replaces items in interlinearized Toolbox texts based on their lexical form as indicated in a replacement table. Currently only replaces part of speech and assumes a particular format of the replacement table.

- `Toolbox_tier_scripts/replace_Toolbox_xx.py` (improved versions) replace items in tier 'xx' in interlinearized Toolbox texts based on their lexical ID and current 'xx' value as indicated in a replacement table. Currently replaceable: \tx, \mb, \ge, \ps.
	- note: it does not seem to work with a single replacement table containing columns pertaining to different tiers, so as a workaround separate Excel tables can be used for every tier. Also, the script reportedly works best when there is a single Excel file in the `Dictionaries` folder.


- `replace_Excel_texts.py` replaces items in annotated Excel spreadsheets based on a replacement table. Currently only replaces part of speech and assumes a particular format of the replacement table.


The following folders are used to store the files used for processing:

- `Corpus_files` contains the interlinearized Toolbox files.

- `Dictionaries` contains the Toolbox dictionaries and replacement tables.

- `Output_files` contains the script outputs (pos tables, new corpus files, new dictionary files).

- `Toolbox_tier_scripts` contains scripts to replace items in individual tiers.
