--DUMMY DATA AS EXAMPLE

WELSPECS
/

COMPDAT
/

WCONPROD
/

GCONPROD
/

--THIS STUFF REALLY NEEDS TO BE FIRST BEFORE ANY INSERTED DATA

-- MODIFIED by schmerge forward model

DATES
 01 JAN 2021 / --ADDED
/

--start templates/gefac.jinja

GEFAC
  OP 0.23 NO /
/

--end templates/gefac.jinja

DATES
  1 JAN 2024 /
/

DATES
  1  JAN 2025 /
/

DATES
 01 DEC 2025 / --ADDED
/

--start templates/wefac.jinja

WEFAC
  '*OP' 0.5 NO /
/

--end templates/wefac.jinja

DATES
  1  JAN 2026 /
/

--THE DATE OF THIS MATTERS

DATES
 01 NOV 2026 / --ADDED
/

--start templates/efac.jinja

WEFAC
  '*OP' 0.8 NO /
/
GEFAC
  OP 0.9 NO /
/

--end templates/efac.jinja

DATES
  1  JAN 2027 /
/

DATES
  1  JAN 2028 /
/
