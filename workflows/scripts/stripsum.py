#!/usr/bin/env python
# Inputs ECL_SUMMARY_FILE, dates_list file
# dates_list file should contain list of dates in the format dd/mm/yyyy
import sys
import os
from ecl.eclfile import EclFile, FortIO
import re
import shutil

summery_file = sys.argv[1]
dates_file = sys.argv[2]

with open(dates_file) as f:
    datelist = [
        (int(date_match[0]), int(date_match[1]), int(date_match[2]))
        for date_match in re.findall('(\d+)\.(\d+)\.(\d+)', f.read())
    ]

filename, file_extension = os.path.splitext(summery_file)
tmp_file_path = filename + "_tmp." + file_extension
shutil.move(summery_file, tmp_file_path)
shutil.copy(filename + ".SMSPEC", filename + "_tmp.SMSPEC")

ecl_file = EclFile(tmp_file_path)
fort_io = FortIO(summery_file, mode=2)

valid_date = True
for kw in ecl_file:
    (tmptype, _, _) = kw.header

    if tmptype == "PARAMS":
        valid_date = (kw[2], kw[3], kw[4]) in datelist
    if tmptype != "SEQHDR" or valid_date:
        kw.fwrite(fort_io)

ecl_file.close()
fort_io.close()
