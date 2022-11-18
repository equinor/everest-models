-- Dummy schedule file - but we try to add a typical set up

WELSPECS
-- Item #: 1	 2	3	4	5	 6
    'PROD1'	'G1'	10	10	8400	'OIL' /
    'PROD2'	'G1'	10	9	8400	'OIL' /
    'PROD3'	'G1'	10	8	8400	'OIL' /
    'INJ1'	'G1'	1	1	8335	'GAS' /
    'INJ2'	'G1'	1	2	8335	'GAS' /
/

COMPDAT
-- Item #: 1	2	3	4	5	6	7	8	9
    'PROD1'	10	10	3	3	'CLOSE'	1*	1*	0.5 /
    'PROD2'	10	9	3	3	'CLOSE'	1*	1*	0.5 /
    'PROD3'	10	8	3	3	'CLOSE'	1*	1*	0.5 /
    'INJ1'	1	1	1	1	'CLOSE'	1*	1*	0.5 /
    'INJ2'	1	2	1	1	'CLOSE'	1*	1*	0.5 /
/

RPTRST
   BASIC=3 FREQ=3 /

-- Adding twelve DATES, once a month

DATES
 01 JAN 2000 /
/

DATES
 01 FEB 2000 /
/

DATES
 23 FEB 2000 / --ADDED
/

--start ./templates/template_welopen.tmpl
WELOPEN
  'PROD1' 'OPEN' /
/

--end ./templates/template_welopen.tmpl


--start ./templates/template_wconprod_oil.tmpl
WCONPROD
  'PROD1' 'OPEN' 'ORAT' 920.0  4*  1000   /
/

--end ./templates/template_wconprod_oil.tmpl


DATES
 01 MAR 2000 /
/

DATES
 01 APR 2000 /
/

DATES
 14 APR 2000 / --ADDED
/

--start ./templates/template_welopen.tmpl
WELOPEN
  'PROD2' 'OPEN' /
/

--end ./templates/template_welopen.tmpl


--start ./templates/template_wconprod_oil.tmpl
WCONPROD
  'PROD2' 'OPEN' 'ORAT' 824.6  4*  1000   /
/

--end ./templates/template_wconprod_oil.tmpl


--start ./templates/template_welopen.tmpl
WELOPEN
  'INJ1' 'OPEN' /
/

--end ./templates/template_welopen.tmpl


--start ./templates/template_wconinje.tmpl
WCONINJE
  'INJ1' 'water' 'OPEN' 'RATE' 550.0 1* 320  1*  1*  1*   /
/

--end ./templates/template_wconinje.tmpl


--start ./templates/template_welopen.tmpl
WELOPEN
  'INJ2' 'OPEN' /
/

--end ./templates/template_welopen.tmpl


--start ./templates/template_wconinje.tmpl
WCONINJE
  'INJ2' 'water' 'OPEN' 'RATE' 1000.0 1* 320  1*  1*  1*   /
/

--end ./templates/template_wconinje.tmpl


DATES
 01 MAY 2000 /
/

DATES
 06 MAY 2000 / --ADDED
/

--start ./templates/template_welopen.tmpl
WELOPEN
  'PROD3' 'OPEN' /
/

--end ./templates/template_welopen.tmpl


--start ./templates/template_wconprod_oil.tmpl
WCONPROD
  'PROD3' 'OPEN' 'ORAT' 1000.0  4*  1000   /
/

--end ./templates/template_wconprod_oil.tmpl


DATES
 01 JUN 2000 /
/

DATES
 02 JUN 2000 / --ADDED
/

--start ./templates/template_wconprod_oil.tmpl
WCONPROD
  'PROD1' 'OPEN' 'ORAT' 880.0  4*  1000   /
/

--end ./templates/template_wconprod_oil.tmpl


DATES
 05 JUN 2000 / --ADDED
/

--start ./templates/template_wconprod_gas.tmpl
WCONPROD
  'INJ1' 'OPEN' 'GRAT' 600.0  4*  1000   /
/

--end ./templates/template_wconprod_gas.tmpl


DATES
 01 JUL 2000 /
/

DATES
 23 JUL 2000 / --ADDED
/

--start ./templates/template_wconprod_gas.tmpl
WCONPROD
  'PROD2' 'OPEN' 'GRAT' 10930.0  4*  1000   /
/

--end ./templates/template_wconprod_gas.tmpl


DATES
 01 AUG 2000 /
/

DATES
 12 AUG 2000 / --ADDED
/

--start ./templates/template_wconinje.tmpl
WCONINJE
  'INJ1' 'water' 'OPEN' 'RATE' 650.0 1* 320  1*  1*  1*   /
/

--end ./templates/template_wconinje.tmpl


DATES
 01 OCT 2000 /
/

DATES
 03 OCT 2000 / --ADDED
/

--start ./templates/template_wconprod_gas.tmpl
WCONPROD
  'INJ1' 'OPEN' 'GRAT' 700.0  4*  1000   /
/

--end ./templates/template_wconprod_gas.tmpl


DATES
 01 NOV 2000 /
/

DATES
 01 DEC 2000 /
/

DATES
 10 DEC 2000 / --ADDED
/


--start ./templates/template_wconinje.tmpl
WCONINJE
  'INJ1' 'water' 'OPEN' 'RATE' 750.0 1* 320  1*  1*  1*   /
/

--end ./templates/template_wconinje.tmpl


DATES
 31 JAN 2001 / --ADDED
/


--start ./templates/template_wconprod_gas.tmpl
WCONPROD
  'INJ1' 'OPEN' 'GRAT' 800.0  4*  1000   /
/

--end ./templates/template_wconprod_gas.tmpl


