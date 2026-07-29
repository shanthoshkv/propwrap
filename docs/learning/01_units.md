# Units (the #1 student trap)

## What went wrong historically

CEA (and RocketCEA) often work in **English** units:

- pressure: **psia**
- temperature: **Rankine**
- c*: **ft/s**

Students paste numbers into SI formulas and get garbage (or worse: plausible garbage).

## What propwrap does

| Quantity | Public unit | Example field |
|----------|-------------|-----------------|
| Pressure | **Pa** | `r.pc_pa` |
| Temperature | **K** | `r.tc_kelvin` |
| Speed / c* | **m/s** | `r.c_star` |
| Density | **kg/m³** | `r.bulk_density_kg_m3` |
| Isp | **s** | `r.isp_vac_shifting` |
| Exhaust velocity | **m/s** | `r.ve_vac_shifting` = Isp × g₀ |

English units are converted **only inside** `cea_backend`.

## How to type pressure without crying

```python
m.evaluate(of=2.56, pc_bar=70, eps=20)   # easiest for homework
m.evaluate(of=2.56, pc_mpa=7, eps=20)
m.evaluate(of=2.56, pc=7_000_000, eps=20)  # pure SI
```

**Never** write `pc=70` meaning bar — that is 70 **pascals** (almost vacuum). propwrap will raise an error if you do this by accident.

## Conversions you will actually need

```python
from propwrap import convert

convert(70, "bar", "Pa")        # 7_000_000
convert(343.7, "s", "m/s")      # Isp → ve
convert(0.81, "g/cm3", "kg/m3") # 810
```

## Exam / viva line

> “I report CEA results in SI: pressure in pascals, temperatures in kelvin, velocities in metres per second. Isp is in seconds by rocketry convention; effective exhaust velocity is Isp times standard gravity.”
