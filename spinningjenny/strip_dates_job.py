import shutil
import os

from ecl.eclfile import EclFile, FortIO
from ecl.summary import EclSum


def process_dates(dates):
    """
    Process a list of dates
    :param dates: list of dates (ex: ['2000-01-01', '2001-02-31', ]
    :return: a list of dates with format [[year, month, day], ..]
    """
    return [[date.year, date.month, date.day] for date in dates]


def strip_dates(summary_file, dates):
    """
    Strips all other dates except the ones given
    :param summary_file: summary file that will be striped of dates other than
    the one given.
    :param dates: list of dates that need to remain in the summary file.
    """
    filename, file_extension = os.path.splitext(summary_file)
    tmp_file_path = filename + "_tmp" + file_extension

    shutil.move(summary_file, tmp_file_path)
    shutil.copy(filename + ".SMSPEC", filename + "_tmp.SMSPEC")

    summary = EclSum(tmp_file_path)
    file_dates = process_dates(summary.dates)

    ecl_file = EclFile(tmp_file_path)
    fort_io = FortIO(summary_file, mode=2)

    valid_date = True
    date_inx = 0
    for kw in ecl_file:
        (tmptype, _, _) = kw.header

        if tmptype == "PARAMS":
            valid_date = file_dates[date_inx] in dates
            date_inx = date_inx + 1
        if tmptype != "SEQHDR" or valid_date:
            kw.fwrite(fort_io)

    ecl_file.close()
    fort_io.close()
