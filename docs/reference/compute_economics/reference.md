
## Economical Indicators

Below are given the general formula of the economical indicator using quite similar naming o the parameters as in the code implementation. Notice that those indicators can be multiplied by a user defined factor. 

First the definition of the discount and comments on the use of a reference case are given.

### Discount

the discount value at a given date, $\text{date}$ (in days), is given by a discount rate, $\text{rate}$, and a reference date, $\text{ref}$ (in days),  as

$$
\text{discount} = \frac{1}{(1+\text{rate})^{(\text{date}-\text{ref})/365.25}}.
$$

### Use of a reference case

Estimation of some delta indicators is possible where the difference between the optimized production and a given single case is used. For example, the reference case can be the mean of the prediction if no new well is drilled (situation as is). This means that in the expressions below, the production would be replaced by


$$
\text{production}_{\text{key}, \text{index}} \leftarrow \text{production}_{\text{key}, \text{index}} - \text{reference_production}_{\text{key}, \text{index}},
$$


where $\text{key}$ is an Eclipse keyword and $\text{index}$ represents the time variable.


### Net Present Value

Implemented formula:

$$
\text{NPV} = \text{gains} - \text{costs},
$$

where $\text{gains}$ are the discounted gains due to production (e.g. oil and gas) and $\text{costs}$ are the discounted costs (e.g. drilling and abandonment costs).
All quantities are interpolated at a daily rate between the start and end date. This means

$$
\text{gains} = \sum_{\text{index} \in \{ \text{time range} \} } \text{discount} \sum_{\text{key} \in  \{ \text{keywords} \} }  
    \text{production}_{\text{key}, \text{index}}
    \times
    \text{price}_{\text{key}, \text{index}},
$$

and

$$
\text{costs} = \sum_{\text{date} \in \{ \text{cost dates} \} } \text{discount} \times \text{costs}_\text{date}.
$$



### Break-Even Price

Implemented formula:

$$
\text{BEP} = \frac{\text{costs}}{\text{production}_\text{oil_eq}},
$$

where $\text{costs}$ are the discounted costs (e.g. drilling and abandonment costs) and $\text{production}_\text{oil_eq}$ is the discounted oil equivalent production.
All quantities are interpolated at a daily rate between the start and end date. This means for the costs part

$$
\text{costs} = \sum_{\text{date} \in \{ \text{cost dates} \} } \text{discount} \times \text{costs}_\text{date}.
$$

The oil equivalent production term (denominator) results of (i) a remapping of the fluid production of the Eclipse summary file into a second set of fluids and (ii)
converting this set of fluids into an oil equivalent. Typically, the dry gas can be converted into sell gas and NLG and then the oil, sell gas and NLG are convertd into
an oil equivalent production. The conversion is given by a set of parameters in the configuration file as

```yaml
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
```

This means the first while FOPT is kept as FOPT, FGPT is remapped as FSGPT and FNLPT with the given coefficients. Notice the keywords are not supposed to only be Eclipse keywords.
Then, in a second step, FOPT, FSGPT and FNLPT are converted into the different contriobutions to a single profile, once more with the given coefficients. In the code implementation, the method `BEPCalculator._get_oil_equivalent`, would thus run for the above example

\begin{align} 
\text{oil_equivalent}_\text{FOPT}  & = 6.289814 \times \text{production}_\text{FOPT}, \\
\text{oil_equivalent}_\text{FSGPT} & = 6.289814 \times 0.001 \times 0.95 \times \text{production}_\text{FGPT}, \\
\text{oil_equivalent}_\text{FNLPT} & = 6.289814 \times 1.9 \times 0.0001 \times\text{production}_\text{FGPT},
\end{align} 

where the factor $6.289814$ corresponds to the conversion from cubic meters to US barrels. Notice this conversion is ALWAYS applied. Then

$$
\text{production}_\text{oil_eq} = \sum_{\text{index} \in \{ \text{time range} \} } \text{discount} \sum_{\text{key} \in  \{ \text{keywords} \} }  
    \text{oil_equivalent}_{\text{key}, \text{index}}.
$$

Notice that the production can be a production difference in case a reference case is given,


!!! danger 

    The code has been tested and used only with the double conversion. No test have been done if for example the oil equivalent would depend only on FOPT and FGPT, nor
    in case the only oil is produced from the field. 


### Observations

The NPV and BEP have been compared to estimation done in a spreadsheet for a given real case. While in the spreadsheet yearly production data were used, the everest_models forward models used a daily interpolation of the production data, prices, exchange rates and discount. This may lead to some noticeable differences.


### Output currency

The output currency is determined by both the existence of a default exchange rate and the given exchange rates. The given exchange rates indicate a rate from the given currency to the default one. This means that the output currency is the one not given in the exchange rate. For a case where both USD and NOK are used currencies in the configuration and that the following echange rate is given 
```yaml
exchange_rates:
    USD:
        - { date: 1997-01-01, value: 5 }
        - { date: 2000-02-01, value: 7 }
        - { date: 2001-05-01, value: 6 }
        - { date: 2002-02-01, value: 9 }
```
the output currency will be NOK.

Notice that it is further possible to overwrite the input configuration by specifying in the command input line one of the currencies given in the exchange rate (eg. USD in the above case).


## Usage and schema


```bash
{!> reference/compute_economics/help!}
```
```yaml
{!> reference/compute_economics/schema.yml!}
```

## Models

$pydantic: everest_models.jobs.fm_compute_economics.economic_indicator_config_model.EconomicIndicatorConfig