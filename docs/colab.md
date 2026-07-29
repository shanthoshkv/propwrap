# Google Colab / cloud backup path

Use this when **lab PCs block installs** or RocketCEA wheels fail locally.

## Limitations

- Colab environments change; pin package versions when possible.  
- FORTRAN / RocketCEA may need extra setup on some runtimes.  
- Prefer a local venv when you can (see [INSTALL.md](INSTALL.md)).

## Sketch notebook cells

**Cell 1 — install**

```python
# May take several minutes
!pip -q install rocketcea cantera pydantic matplotlib numpy
# If you uploaded/cloned propwrap:
# !pip -q install -e /content/propwrap
```

If you only need CEA via RocketCEA without the full package:

```python
from rocketcea.cea_obj import CEA_Obj
C = CEA_Obj(oxName="LOX", fuelName="RP1")
print(C.get_Isp(Pc=70*14.5037738, MR=2.56, eps=20))  # English Pc!
```

**Cell 2 — full propwrap (after clone)**

```python
!git clone https://github.com/shanthoshkv/propwrap.git
%cd propwrap
!pip -q install -e .
```

```python
from propwrap import Mixture
print(Mixture("RP-1", "LOX").evaluate(of=2.56, pc_bar=70, eps=20))
```

## If RocketCEA will not install on Colab

1. Use a local machine/venv.  
2. Or use NASA CEAWeb for hand calculations and still learn propwrap concepts from the docs.  
3. Ask your TA for a pre-built environment.

## Student note

Document in your report which environment you used (local venv version vs Colab).
