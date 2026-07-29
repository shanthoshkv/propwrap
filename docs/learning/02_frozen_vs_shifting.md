# Frozen vs shifting equilibrium

## The short version

When combustion products expand in a nozzle, their **chemical composition** may or may not keep changing.

| Mode | Assumption | Isp |
|------|------------|-----|
| **Shifting** | Composition re-equilibrates as T and P drop | Usually **higher** |
| **Frozen** | Composition freezes (often near throat/chamber) | Usually **lower** |

propwrap always reports **both**.

```python
r = Mixture("RP-1", "LOX").evaluate(of=2.56, pc_bar=70, eps=20)
print(r.isp_vac_shifting, r.isp_vac_frozen)
```

## What is “real”?

Reality is **between** frozen and shifting:

- Large nozzles, slow chemistry → closer to frozen  
- Fast kinetics, high T → closer to shifting  

For student reports, say:

> Shifting provides an optimistic bound; frozen a conservative bound. Flight engines include additional losses not in ideal CEA.

## Optional rough delivered Isp

```python
m = Mixture("RP-1", "LOX", efficiency=(0.98, 0.97))  # ηc*, ηCf
r = m.evaluate(of=2.56, pc_bar=70, eps=20)
print(r.isp_vac_delivered)  # rough only
```

Do **not** invent efficiencies without a source.

## Viva answer

> “CEA shifting equilibrium allows composition to change along the nozzle; frozen freezes composition. Real engines sit between them and also lose performance to incomplete combustion and nozzle losses.”
