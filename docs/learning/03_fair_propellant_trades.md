# Fair propellant trades

## The classic mistake

```text
Compare RP-1/LOX, CH4/LOX, LH2/LOX all at O/F = 2.5
```

That is **unfair**:

| Pair | Sensible O/F band |
|------|-------------------|
| LOX / RP-1 | ~2.0–2.8 |
| LOX / CH₄ | ~2.5–3.6 |
| LOX / LH₂ | ~4.5–6.5 |

At O/F = 2.5, hydrogen is far from its best operating point.

## The right approach

**Optimise O/F for each pair**, then compare the winners.

```python
from propwrap import compare_propellants

trade = compare_propellants(
    ["RP-1/LOX", "CH4/LOX", "LH2/LOX"],
    pc_bar=70,
    eps=40,
)
print(trade)
```

You get:

1. Each pair’s **optimum O/F** (for vac Isp)  
2. Ranking by **Isp**  
3. Ranking by **density-Isp** (ρ × Isp) — tanks matter  

## Isp vs density-Isp

| Metric | Favours |
|--------|---------|
| High Isp | Often LH₂ (high energy per mass) |
| High ρ·Isp | Often RP-1 (dense, smaller tanks) |

Neither is “always better.” State the mission (volume-limited vs mass-limited).

## CLI

```bash
propwrap compare-pairs --combos "RP-1/LOX,CH4/LOX,LH2/LOX" --pc-bar 70 --eps 40
```

Avoid fixed-O/F `propwrap compare` unless your assignment forces one O/F.

## Viva answer

> “A fair propellant trade maximises performance for each combination over mixture ratio at the same Pc and ε, rather than forcing one O/F on chemistries with different stoichiometry.”
