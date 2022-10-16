import datetime
import logging
import os
import shutil
from typing import List

from ecl.eclfile import EclFile, FortIO
from ecl.summary import EclSum

logger = logging.getLogger(__name__)


def process_dates(dates):
    """
    Process a list of dates
    :param dates: list of dates (ex: ['2000-01-01', '2001-02-31', ]
    :return: a list of dates with format [[year, month, day], ..]
    """
    return [[date.year, date.month, date.day] for date in dates]


def strip_dates(
    summary_file: EclSum, dates: List[List[int]], allow_missing_dates: bool = False
):
    """
    Strips all other dates except the ones given
    :param summary_file: summary file that will be stripped of dates other than
    the one given.
    :param dates: list of dates that need to remain in the summary file. A date
    is a list with exactly three integers, year, month, day.
    :allow_missing_dates: if true, do not raise a runtime error on missing dates.
    """
    try:
        summary = EclSum(summary_file)
    except:
        raise RuntimeError(f"Not an eclipse file: {summary_file}")

    summary_dates = process_dates(
        [np_date.astype(datetime.datetime) for np_date in summary.numpy_dates]
    )
    missing_dates = [date for date in dates if date not in summary_dates]
    if missing_dates:
        isoformatted_datelist = ", ".join(
            datetime.date(*date).isoformat() for date in missing_dates
        )
        msg = (
            f"Missing date(s): {isoformatted_datelist}, "
            f"in eclipse file: {summary_file}"
        )

        if allow_missing_dates:
            logger.warning(msg)
        else:
            raise RuntimeError(msg)

    filename, file_extension = os.path.splitext(summary_file)
    tmp_file_path = filename + "_BAK" + file_extension

    shutil.move(summary_file, tmp_file_path)
    shutil.copy(filename + ".SMSPEC", filename + "_BAK.SMSPEC")

    ecl_file = EclFile(tmp_file_path)
    fort_io = FortIO(summary_file, mode=2)

    file_dates = process_dates(summary.dates)

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
