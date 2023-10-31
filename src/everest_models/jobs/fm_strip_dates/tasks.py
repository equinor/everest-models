import datetime
import logging
import os
import shutil
from typing import List

from resdata.resfile import FortIO, ResdataFile

logger = logging.getLogger(__name__)

SPEC_EXTENSION = "SMSPEC"


def strip_dates(
    summary_dates: List[datetime.datetime],
    dates: List[datetime.date],
    summary_path: str,
):
    """Strip all other dates except the ones given from eclipse summary.

    Args:
        summary_dates: Eclipse summary dates
        dates (List[datetime.date]): dates to whitelist from strip
        summary_path (str): eclipse summary filepath
    """
    base_path, extension = os.path.splitext(summary_path)
    temp_path = f"{base_path}_BAK.{extension}"

    shutil.move(summary_path, temp_path)
    shutil.copy(f"{base_path}.{SPEC_EXTENSION}", f"{base_path}_BAK.{SPEC_EXTENSION}")

    ecl_file = ResdataFile(temp_path)
    fort_io = FortIO(summary_path, mode=2)

    valid_date = True
    date_inx = 0
    for kw in ecl_file:
        tmptype, _, _ = kw.header

        if tmptype == "PARAMS":
            valid_date = summary_dates[date_inx].date() in dates
            date_inx = date_inx + 1
        if tmptype != "SEQHDR" or valid_date:
            kw.fwrite(fort_io)

    ecl_file.close()
    fort_io.close()
