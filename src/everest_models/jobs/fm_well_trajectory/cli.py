import logging
from pathlib import Path

from .outputs import write_guide_points, write_mlt_guide_md, write_mlt_guide_points
from .parser import build_argument_parser
from .read_trajectories import read_trajectories
from .well_trajectory_resinsight import well_trajectory_resinsight
from .well_trajectory_simple import well_trajectory_simple

logger = logging.getLogger(__name__)

FULL_JOB_NAME = "Well trajectory"

EXAMPLES = """
Argument examples
~~~~~~~~~~~~~~~~~

:code:`-c, --config` example

.. code-block:: yaml

    interpolation:
        type: resinsight
        measured_depth_step: 5.0

    connections:
        type: resinsight
        formations_file: ./formations.lyr
        perforations:
            - well: INJ
              formations: [3, 4]
            - well: PROD
              formations: [1, 2, 3, 4]
              static:
                - key: PORO
                  min: 0
                  max: 1
              dynamic:
                - key: SWAT
                  min: 0
                  max: 0.5
                  date: 2015-01-02

    wells:
        - name: INJ
          group: G1
          phase: GAS
          platform: PLATFORM1
          dogleg: 4
          skin: 0
          radius: 0.15
        - name: PROD
          group: G1
          phase: OIL
          platform: PLATFORM2
          dogleg: 4
          skin: 0
          radius: 0.15

    platforms:
        - name: PLATFORM1
          x: 6000
          y: 4000
          k: 50
        - name: PLATFORM2
          x: 5000
          y: 5000
          k: 50

Formation layer file example

.. code-block:: text

    'formation1' 1-1
    'formation2' 2-2
    'formation3' 3-4
    'formation4' 5-5

Output file examples
~~~~~~~~~~~~~~~~~~~~

:code:`PROD.dev` Part of well trajectory deviation file (interpolated well trajectory)

.. code-block:: text

    WELLNAME: 'PROD'
    #       X           Y      TVDMSL       MDMSL
      5000.00     5000.00        0.00        0.00
      5000.00     5000.00        4.98        5.00
      5000.00     5000.00        9.96       10.00
    ...
      5920.02     6079.98     8516.36     8640.00
      5920.03     6079.99     8521.36     8645.00
      5920.04     6080.00     8525.00     8648.64
    -999

:code:`PROD.SCH` Well completion information

.. code-block:: text

    -- WELL  GROUP        BHP    PHASE  DRAIN  INFLOW  OPEN  CROSS  PVT    HYDS  FIP
    -- NAME  NAME   I  J  DEPTH  FLUID  AREA   EQUANS  SHUT  FLOW   TABLE  DENS  REGN
    WELSPECS
       PROD  G1     6  7  1*     OIL    0.0    STD     STOP  YES    0      SEG   0    /
    /
    -- WELL                     OPEN   SAT   CONN           WELL      KH             SKIN      D      DIR
    -- NAME   I   J   K1   K2   SHUT   TAB   FACT           DIA       FACT           FACT      FACT   PEN
    COMPDAT
       PROD   6   7   1    1    OPEN   1*    7.462625E+01   0.30000   1.000757E+04   0.00000   1*     'Z' /
       PROD   6   7   2    2    OPEN   1*    1.118596E+01   0.30000   1.500165E+03   0.00000   1*     'Z' /
       PROD   6   7   3    3    OPEN   1*    7.456390E+01   0.30000   9.999988E+03   0.00000   1*     'Z' /
    /

"""


def main_entry_point(args=None):
    args_parser = build_argument_parser()
    options = args_parser.parse_args(args)

    if options.lint:
        args_parser.exit()

    guide_points = read_trajectories(
        options.config.wells,
        options.config.platforms,
    )
    logger.info("Writing guide points to 'guide_points.json'")
    write_guide_points(guide_points, Path("guide_points.json"))

    if options.config.interpolation.type == "simple":
        well_trajectory_simple(
            options.config.wells,
            options.config.interpolation,
            options.config.npv_input_file,
            guide_points,
        )

    # resinsight
    if options.config.connections:
        if (
            eclipse_model := options.eclipse_model or options.config.eclipse_model
        ) is None:
            args_parser.error("Missing eclipse model")

        for e in options.config.connections.perforations:
            if bool(e.dynamic) and not Path(f"{eclipse_model}.UNRST").exists():
                args_parser.error(f"Missing {eclipse_model}.UNRST file")

        if not Path(f"{eclipse_model}.EGRID").exists():
            args_parser.error(f"Missing {eclipse_model}.EGRID file")

        if not Path(f"{eclipse_model}.INIT").exists():
            args_parser.error(f"Missing {eclipse_model}.INIT file")

        mlt_guide_points = well_trajectory_resinsight(
            options.config, eclipse_model, guide_points
        )
        if mlt_guide_points:
            logger.info("Writing multilateral guide points to 'mlt_guide_points.json'")
            write_mlt_guide_points(mlt_guide_points, Path("mlt_guide_points.json"))
            logger.info("Writing multilateral guide md's to 'mlt_guide_md.json'")
            write_mlt_guide_md(mlt_guide_points, Path("mlt_guide_md.json"))
