## Smart Zone Calculator

Integration that will calculate watering zone runtime given:

- Calculated ETO requirement sensor (mm)
- Rain over period sensor (mm)
- Watering throughput of the zone (mm/h)
- Zone scale factor (%)
- Max zone run time (mins)

Calculations as follows:

```
delta = rain over period - calculated ETO requirement
if delta < 0 then
    # Watering required
    runtime = abs(delta) / throughput * 3600 * scale factor (seconds)
    if (reqd * 60) > max zone run time
        runtime = max zone run time * 60
else
    runtime = 0
```