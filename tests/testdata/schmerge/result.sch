RPTRST
   BASIC=3 FREQ=3 /

-- MODIFIED by schmerge forward model

DATES
 01 JAN 2000 / --ADDED
/

--start files/wconinje.jinja

WCONINJE
  'INJECT7'  'WATER'  'OPEN'  'RATE' 0.7   1* 320  1*  1*    1*   /
/

--end files/wconinje.jinja

DATES
 30 MAY 2014 /
/

-- DATES is typically commented out,
-- let's demonstrate that behaviour as well

--DATES
-- 26 OKT 2014 /
--/

DATES
 28 AUG 2014 /
/

DATES
 26 NOV 2014 /
/

DATES
 24 FEB 2015 /
/

DATES
 25 MAY 2015 /
/

DATES
 23 AUG 2015 /-- This is a comment
/

DATES -- this too
 21 NOV 2015 /-- 22 NOV 2015 /
/

DATES
 19 FEB 2016 /
/

DATES
-- 18 MAY 2016
 19 MAY 2016 /
/

-- this END limits the life cycle period to 5 years instead of 10
END

--start files/welopen.jinja

WELOPEN
  'INJECT5' 'OPEN' /
/

--end files/welopen.jinja

DATES
 20 MAY 2016 / --ADDED
/

--start files/welopen.jinja

WELOPEN
  'PROD3' 'OPEN' /
/

--end files/welopen.jinja

DATES
 17 AUG 2016 /
/ -- DATES

DATES
 15 NOV 2016 /
/

DATES
 13 FEB 2017 /
/

DATES
 01 APR 2017 /
/

GSATPROD
 'DOPSAT' 319.3006994 2008.845173 913164.7543 /
/

--start files/wconinje.jinja

WCONINJE
  'INJECT7'  'GAS'  'OPEN'  'RATE' 2500000.0   1* 320  1*  1*    1*   /
/

--end files/wconinje.jinja

DATES
 14 MAY 2017 /
/

DATES
 12 AUG 2017 /
/

DATES
 10 NOV 2017 /
/

DATES
 8 FEB 2018 /
/

DATES
 01 MAR 2018 /
/

WEFAC
 '*HAOP' 0.832 /
 '*HAWI' 0.49 /
/

GSATPROD
 'DOPSAT' 84.723817 214.0727 111269.15 /
/

--start files/wconinje.jinja

WCONINJE
  'INJECT5'  'GAS'  'OPEN'  'RATE' 2500000.0   1* 320  1*  1*    1*   /
/

--end files/wconinje.jinja

DATES
 9 MAY 2018 /
/

DATES
 7 AUG 2018 /
/

DATES
 5 NOV 2018 /
/

DATES
 3 FEB 2019 /
/

DATES
 4 MAY 2019 /
/

DATES
 2 AUG 2019 /
/

DATES
 31 OCT 2019 /
/

DATES
 28 JAN 2020 / --ADDED
/

--start files/welopen.jinja

WELOPEN
  'INJECT1' 'OPEN' /
/

--end files/welopen.jinja

DATES
 29 JAN 2020 /
/

DATES
 28 APR 2020 /
/

DATES
 27 JUL 2020 /
/

DATES
 28 JLY 2020 /
/

--start files/welopen.jinja

WELOPEN
  'PROD4' 'OPEN' /
/

--end files/welopen.jinja

DATES
 25 OCT 2020 /
/

DATES
 23 JAN 2021 /
/

DATES
 23 APR 2021 /
/

END

--start files/welopen.jinja

WELOPEN
  'PROD1' 'OPEN' /
/

--end files/welopen.jinja

DATES
 24 APR 2021 / --ADDED
/

--start files/wconinje.jinja

WCONINJE
  'INJECT3'  'GAS'  'OPEN'  'RATE' 0.55   1* 320  1*  1*    1*   /
/

--end files/wconinje.jinja

