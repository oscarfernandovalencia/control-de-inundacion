# Information Usage & Cross-Project Integration Rules — `control-de-inundacion`

> **Source of Truth**: Mirror of [`LEEME.md`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/LEEME.md) and [`rules/uso-de-informacion.md`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/rules/uso-de-informacion.md) (Spanish).

## 1. Project Definition & Context
- **Scope**: Pre-design, Unit Price Analysis (APU) budgeting, technical presentation, and construction execution of two complementary drainage works to solve flooding in a rural house in Eastern Antioquia (*Oriente Antioqueño*), scheduled for November:
  1. **French Drain (*Filtro Francés*)**: Base length $L_{filtro} = 30.0\text{ ml}$, trench width $W = 0.40\text{ m}$, depth $H = 0.80\text{ m}$, clean gravel height $h_g = 0.60\text{ m}$, top cover $h_c = 0.20\text{ m}$, NT 1600/1800 non-woven geotextile, and 4" perforated drainage pipe.
  2. **Crown Ditch (*Ronda / Cuneta de Coronación*)**: Base length $L_{ronda} = 40.0\text{ ml}$, trapezoidal section lined with $2500\text{ PSI}$ ($17.2\text{ MPa}$) concrete ($e = 7.5\text{ cm}$), reinforced with M-084 / Q-106 welded wire mesh and waterproofing admixture (Sika 1).
- **Commercial Goal**: Win the construction contract with a competitive, fair price that protects contractor margins (zero financial loss), deliver high-quality engineering work, and establish a reusable parametric baseline to rapidly design and quote similar drainage/flood-control projects.

## 2. Information Organization & Cross-Project Sharing
- Centralize all budget data (`Presupuesto Filtro.ods`, `datos_presupuesto.json`), presentations (`Presentación Filtro.odp`), and parametric software (`app_presupuesto_filtro.py`) in this directory.
- Maintain standardized input catalogs (23 base inputs across Equipment, Labor, Transport, and Materials) so unit prices and yields can be cross-referenced and shared with other projects in `/home/v1rr3eor/IAs/projects/`.
