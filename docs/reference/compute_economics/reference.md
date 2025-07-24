*******************************
Introduction
*******************************

The EVEREST compute-economics module compares the economic performance of an investment against a reference case. This functionality is particularly useful for evaluating project value and supporting investment decisions. For example, if a new production well is drilled in an existing field, the module can assess how much additional economic value - typically measured in Net present value (NPV) - is generated relative to a base case.

In addition, the module calculates the break-even price, which is defined as the minimum price per barrel required for an investment to recover the investment costs. This metric helps compare different options, understands how sensitive a project is to changes in price or cost, and enables more precise and robust decisions.




Use of a reference case
=================

The results of an optimized development scenario can be compared to a reference case. A typical reference case might involve a forecast assuming that no additional wells are drilled, representing the baseline or "as-is" scenario. The difference in production is calculated by subtracting the production volumnes of the reference case from the optimized case.

.. math::
    \Delta production_{key, index} = optimized\ production_{key, index} - reference\ production_{key, index}


where :math:`{key}` denotes, depending on the user-defined input option, the selected fluid volume variables :math:`{FOPT}` and :math:`{FGPT}`, and optionally cost-related terms such as :math:`{FWPT}`, :math:`{FWIT}`, and/or :math:`{FGIT}`. The variable :math:`{index}` reflects the time step.



Net Present Value
=================

The Net Present Value (NPV) is defined as the difference between the discounted gains and the discounted costs:

.. math::

   \text{NPV} = \text{gains} - \text{costs}


In this context, the gains refer to the discounted incremental production revenues, computed from the difference in production for each key (e.g., oil, gas, water) at each time step. The costs refer to the discounted expenditures associated with the project, such as drilling, completion, or abandonment costs.


All quantities are interpolated depending on the reported Eclipse time sreps between the start and end dates of the evaluation period. The gains are calculated as:


.. math::

   gains = \sum_{index \in \{ time\ range \}} discount \sum_{key \in \{ keywords \}} 
       \Delta production_{key,\ index} \times price_{key,\ index}


.. math::

   costs = \sum_{date \in \{ cost\ dates \}} discount \times costs_{date}


Discount
=================


The discount factor corresponding to :math:`{date}` (expressed in days) is computed based on a discount rate :math:`{rate}` and a reference date :math:`{ref}` (also in days)


.. math::

   discount = \frac{1}{(1 + rate)^{(date - ref) / 365.25}}



*******************************
Break-Even Price
*******************************

The break-even price module relates the total oil-equivalent volume to the investment cost. In a first step, the oil equivalent volume in barrels are estimated using the equations below.The total oil production :math:`{FOPT}` is converted from cubic meters to barrels using a standard factor of 6.289814. In addition, the total gas production :math:`{FGPT}` is used to estimate oil equivalents from both separator gas and natural gas liquids. For separator gas :math:`{FGSPT}`, the volume is scaled to 1,000 Sm³, adjusted with an energy correction factor of 0.95, and then converted to barrels. For natural gas liquids :math:`{FNLPT}`, the volume is estimated by assuming that 1.9 m³ of NGLs are recovered per 10,000 Sm³ of produced gas, and then converted from cubic meters to barrels.


.. math::

   oil\ equivalent_{FOPT}  = 6.289814 \times \Delta production_{FOPT}, \\

   oil\ equivalent_{FSGPT} = 6.289814 \times 0.001 \times 0.95 \times \Delta production_{FGPT}, \\

   oil\ equivalent_{FNLPT} = 6.289814 \times 1.9 \times 0.0001 \times \Delta production_{FGPT}

   oil\ equivalent = oil\ equivalent_{FOPT} + oil\ equivalent_{FSGPT} + oil\ equivalent_{FNLPT}


Break-Even formulation
=================

The break-even price is then determined by

.. math::

   BEP = \frac{costs}{oil\ equivalent}

where :math:`costs` represents the discounted capital expenditures, and :math:`oil\ equivalent` is the discounted oil-equivalent production.





*******************************
Configuration example
*******************************

The prices section defines the input prices for FOPT, FWPT, FGPT, FWIT, and FGIT. Each price entry is associated with a specific date, which affects the results if a discount rate is applied. Negative values represent costs. IF bep_consider_opex is set to True, the FWPT, FWIT, and FGIT are considered as costs in the calculation of the break-even price. Moreover, wellcosts and other costs can be included. 


prices:
    FOPT:
        - { date: 2030-01-01, value: 420, currency: USD }
    FWPT:
        - { date: 2030-01-01, value: -6.3, currency: USD }
    FGPT:
        - { date: 2030-01-01, value: 0.4, currency: USD }
    FWIT:
        - { date: 2030-01-01, value: -6.3, currency: USD }

bep_consider_opex: 
    False

discount_rates:
    - { date: 2030-01-01, value: 0.00 }

well_costs:
   - { well: A-3B-S, value: 20e6, currency: USD }

costs:
   - { date: 2030-01-01, value: 20e6, currency: USD }


----------------------------




The output currency can be dynamically based on the default exchange rate and any user-provided exchange rates. For example, if USD is the default currency and an exchange rate from NOK to USD is provided, the output currency will be NOK and updated annually.


exchange_rates:
    USD:
        - { date: 1997-01-01, value: 5 }
        - { date: 2000-02-01, value: 7 }
        - { date: 2001-05-01, value: 6 }
        - { date: 2002-02-01, value: 9 }
----------------------------



The keyword oil_equivalent is used to define the conversion factors for oil and gas production into oil equivalents. The conversion factors are applied to the production volumes of FOPT, FSGPT, and FNLPT. The remap section allows for adjusting the conversion factors based on the specific requirements of the analysis.



oil_equivalent:
    oil:
        FOPT: 1.0
        FSGPT: 0.001
        FNLPT: 1.9
    remap:
        FOPT:
           FOPT: 1.0
        FGPT:
           FSGPT: 0.95
           FNLPT: 0.0001