import datetime
import re

_ECLIPSE_DATE_REGEX = re.compile(
    r"""
^DATES                                                          # Starting token
(?:[^/]*\n)+                                                    # Arbitrary line separator
\s*
(?P<day>\d{1,2})\s+                                             # Capture day of the month
(?P<quote>['"]?)                                                # Maybe enclosed in quotes
(?P<month>JAN|FEB|MAR|APR|MAY|JUN|JLY|JUL|AUG|SEP|OCT|NOV|DEC)  # Capture locale's abbreviation month
(?P=quote)\s+                                                   # Maybe enclosed in quotes
(?P<year>\d{4})                                                 # Capture year with century
(?:\s+
(?:\d{2}:\d{2}):\d{2}(?:\.\d{4})?)?                             # Ignore time (hours:minute:second.millisecond) 
\s*/
(?:[^/]*\s)+                                                    # Arbitrary line separator
/
(?:(?:[^/]*\n)+END(?:[^/]\n)*)?                                 # Trailing END token
""",
    re.VERBOSE + re.MULTILINE,
)


class EclipseDateMatch:
    def __init__(self, match: re.Match) -> None:
        self._match = match

    @property
    def date(self) -> datetime.date:
        return datetime.datetime.strptime(
            f"{self._match['day']} "
            + (month if (month := self._match["month"]) != "JLY" else "JUL")
            + f" {self._match['year']}",
            "%d %b %Y",
        ).date()

    @property
    def value(self):
        return self._match[0]

    @property
    def for_insertion(self):
        return False


def eclipse_dates(content: str):
    return [
        EclipseDateMatch(match)
        for match in _ECLIPSE_DATE_REGEX.finditer(
            content,
        )
    ]
