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
 01 MAR 2000 /
/

DATES
 01 APR 2000 /
/

DATES
 01 MAY 2000 /
/

DATES
 01 JUN 2000 /
/

DATES
 01 JUL 2000 /
/

DATES
 01 AUG 2000 /
/

DATES
 01 OCT 2000 /
/

DATES
 01 NOV 2000 /
/

DATES
 01 DEC 2000 /
/
