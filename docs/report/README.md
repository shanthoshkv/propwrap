# propwrap technical report (LaTeX)

Industry-style engineering report for the full **propwrap** project.

| File | Description |
|------|-------------|
| `propwrap_technical_report.tex` | Full LaTeX source |
| `propwrap_technical_report.pdf` | Compiled PDF (after build) |

## Build

Requires a TeX distribution (MiKTeX / TeX Live) with common packages (`amsmath`, `siunitx`, `natbib`, `hyperref`, `listings`, …).

```bash
cd docs/report
pdflatex propwrap_technical_report.tex
pdflatex propwrap_technical_report.tex
```

Or:

```bash
latexmk -pdf propwrap_technical_report.tex
```

## Contents (outline)

1. Introduction and motivation  
2. Scope (in / out)  
3. Theoretical background (all main formulae: $F$, $I_{sp}$, $v_e$, $c^*$, $C_f$, $\varepsilon$, density impulse, …)  
4. Units and metrology (SI contract, $g_0$, bar)  
5. Software architecture  
6. Public API, CLI, student tooling  
7. Validation (CEA goldens, physics identities, regression matrix)  
8. Worked examples  
9. Limitations  
10. Conclusions + references  

Aligned with software **v0.1.3**.
