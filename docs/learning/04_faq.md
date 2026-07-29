# FAQ (students)

## My CEA Isp is higher than the engine on Wikipedia. Did I break something?

**Usually no.** Wikipedia (and company brochures) quote **delivered / flight** Isp.  
propwrap quotes **ideal CEA theoretical** Isp. Delivered is often ~90–98% of ideal (sometimes less for old engines).

Write in your report: *theoretical vs delivered*.

## Why is peak Isp not at stoichiometric O/F?

For many LOX/hydrocarbon systems, the **vacuum Isp peak is fuel-rich** of stoich.  
Molecular weight, γ, and temperature trade off; pure stoich maximises temperature, not always Isp.

## What is density impulse?

\[
\rho\text{-}I_{sp} = I_{sp} \times \rho_{\text{bulk}}
\]

with bulk density from liquid fuel + oxidizer at the given O/F.  
High ρ·Isp → more impulse per tank volume.

## Do I need plots?

No. Plots are **opt-in**:

```python
sweep.plot(save="fig.png")
```

## Can I use this for my flight engine design review?

Use it for **preliminary propellant analysis** and method discussion.  
It is **not** flight-certified software.

## Frozen or shifting — which do I put in the abstract?

Report **both**, or report shifting and mention frozen as a lower bound, unless your course specifies one.

## `pc=70` crashed / warned. Why?

`pc` is **pascals**. 70 Pa is tiny. Use `pc_bar=70`.

## How do I hand in homework?

```bash
propwrap homework kerolox --name YourName
```

Zip the generated folder (includes assumptions, CSV, plots, summary.md).
