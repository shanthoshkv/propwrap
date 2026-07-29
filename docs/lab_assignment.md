# Sample lab assignment — Liquid propellant performance with propwrap

**Course:** Rocket propulsion / aerospace thermo (adapt as needed)  
**Duration:** 1 lab session + short write-up  
**Tool:** [propwrap](https://github.com/shanthoshkv/propwrap)  

---

## Learning outcomes

By the end of this lab you will be able to:

1. Install and run a Python thermochemistry library in a virtual environment.  
2. Compute theoretical vacuum Isp, c*, and chamber temperature for a bipropellant pair.  
3. Find an optimum mixture ratio from an O/F sweep.  
4. Compare propellants fairly (each at its own optimum O/F).  
5. Distinguish theoretical CEA results from flight-delivered engine data.  

---

## Prelab (15 min)

1. Read [INSTALL.md](INSTALL.md) and install propwrap.  
2. Skim [learning/02_frozen_vs_shifting.md](learning/02_frozen_vs_shifting.md) and [learning/03_fair_propellant_trades.md](learning/03_fair_propellant_trades.md).  
3. Answer: *Why might Wikipedia’s Merlin Isp be lower than your CEA number?*  

---

## Procedure

### Part A — Design point (25%)

```bash
propwrap homework kerolox --name YOUR_NAME
```

Open `summary.md` and `assumptions.txt`.

Record in your report:

| Quantity | Value | Unit |
|----------|------:|------|
| O/F | | — |
| Pc | | bar or Pa |
| ε | | — |
| Isp vac shifting | | s |
| Isp vac frozen | | s |
| ve | | m/s |
| c* | | m/s |
| Tc | | K |

### Part B — O/F scan (30%)

Using the generated O/F plot and CSV:

1. State the **optimum O/F** for max vacuum Isp.  
2. Is it fuel-rich or oxidizer-rich of stoich (if stoich is shown/known)?  
3. Estimate Isp loss if O/F is ±0.2 from optimum.  

### Part C — Fair trade (30%)

From the trade section/plot (or run):

```bash
propwrap compare-pairs --combos "RP-1/LOX,CH4/LOX,LH2/LOX" --pc-bar 70 --eps 40
```

1. Rank pairs by Isp.  
2. Rank by density-Isp.  
3. One paragraph: which would you pick for (a) maximum Δv mass-limited, (b) volume-limited stage?  

### Part D — Reflection (15%)

Answer discussion prompts in `summary.md`. Include the sentence:

> Results are ideal CEA theoretical performance, not flight-delivered Isp.

---

## Deliverables

Zip the homework folder plus a short PDF/Word report (2–4 pages) with:

- Filled table (Part A)  
- Two figures with captions (use `captions.txt`)  
- Answers B–D  

---

## Marking rubric (example)

| Criterion | Points |
|-----------|-------:|
| Correct install + reproducible numbers | 15 |
| Units correct (Pa/K/m/s; Isp in s) | 15 |
| O/F optimum identified and discussed | 25 |
| Fair trade reasoning | 25 |
| Theoretical vs delivered clarity | 10 |
| Clarity / figures / captions | 10 |
| **Total** | **100** |

---

## Academic integrity

You may discuss concepts with classmates.  
Submitted numbers and write-up must be your own run and your own words.  
Do not fabricate CEA outputs.
