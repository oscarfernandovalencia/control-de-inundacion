# 💧 Control de Inundación — Filtro Francés y Ronda de Coronación

> **Directrices del Proyecto (Español)**: Ver [`LEEME.md`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/LEEME.md) y [`rules/uso-de-informacion.md`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/rules/uso-de-informacion.md).  
> **AI Context Mirror (English)**: See [`rules/information-usage.md`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/rules/information-usage.md).

## 1. Descripción General del Proyecto
Proyecto de ingeniería civil y construcción programado para el mes de **noviembre** en un predio rural ubicado en un municipio del **Oriente Antioqueño**, orientado a solucionar de raíz el problema de inundación y humedad por escorrentía superficial e infiltración subsuperficial hacia una vivienda rural mediante dos obras complementarias:
1. **Capítulo I — Construcción de Filtro Francés (Subdrenaje Perimetral)**:
   - **Longitud base prediseñada**: $L_{filtro} = 30.0\text{ ml}$ (ajustable en visita técnica).
   - **Sección típica**: Zanja de ancho $W = 0.40\text{ m}$ y profundidad $H = 0.80\text{ m}$, con pendiente longitudinal del $1\%$ al $2\%$.
   - **Componentes**: Geotextil no tejido NT 1600 / NT 1800, tubería corrugada perforada de drenaje $\varnothing 4"$, medio filtrante en grava triturada limpia ($3/4"$ a $1\text{-}1/2"$, altura $h_g = 0.60\text{ m}$) y capa superior de cierre/protección ($h_c = 0.20\text{ m}$).
2. **Capítulo II — Construcción de Ronda o Cuneta de Coronación**:
   - **Longitud base prediseñada**: $L_{ronda} = 40.0\text{ ml}$ en cabecera de ladera + caballón de tierra.
   - **Sección típica**: Trapezoidal (base menor $b = 0.30\text{ m}$, taludes laterales de $0.41\text{ m}$, excavación de $0.40\text{ m}$).
   - **Estructura**: Revestimiento en concreto hidráulico de $2500\text{ PSI}$ ($17.2\text{ MPa}$) de espesor $e = 7.5\text{ cm}$ impermeabilizado con Sika 1, reforzado con malla electrosoldada M-084 / Q-106 y juntas de dilatación selladas.

---

## 2. Archivos del Repositorio

| Archivo | Descripción |
| :--- | :--- |
| [`Presupuesto Filtro.ods`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/Presupuesto%20Filtro.ods) | Libro de cálculo en LibreOffice Calc con 3 hojas vinculadas: `01_PRESUPUESTO`, `02_APU` y `03_INSUMOS`. |
| [`Presentación Filtro.odp`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/Presentaci%C3%B3n%20Filtro.odp) | Presentación comercial y técnica para el cliente (Diagnóstico, Diseño Técnico y Propuesta Económica). |
| [`app_presupuesto_filtro.py`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/app_presupuesto_filtro.py) | **Aplicación en Python (GUI CustomTkinter + CLI)** para gestión de presupuesto APU, cálculo del **Valor Total de la Mano de Obra**, edición de precios de insumos, ajuste geométrico y sincronización con `.ods`. |
| [`datos_presupuesto.json`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/datos_presupuesto.json) | Base de datos estructurada en JSON (23 insumos, parámetros geométricos y porcentajes de AIU) compartible con otros proyectos. |
| [`Reporte_Presupuesto_y_Mano_de_Obra.md`](file:///home/v1rr3eor/IAs/projects/control-de-inundacion/Reporte_Presupuesto_y_Mano_de_Obra.md) | Informe detallado autogenerado con el desglose financiero, mano de obra por actividad/cuadrilla y lista comercial de compras. |

---

## 3. Cómo Ejecutar la Aplicación en Python (`app_presupuesto_filtro.py`)

### Opción A: Interfaz Gráfica Completa (GUI Desktop con CustomTkinter)
```bash
/home/v1rr3eor/IAs/projects/AplicacionesIngenieria/venv/bin/python app_presupuesto_filtro.py
```

### Opción B: Menú Interactivo en Consola (`--cli`)
```bash
/home/v1rr3eor/IAs/projects/AplicacionesIngenieria/venv/bin/python app_presupuesto_filtro.py --cli
```

### Opción C: Reporte Rápido y Sincronización con `.ods` (`--resumen` / `--sync-ods`)
```bash
/home/v1rr3eor/IAs/projects/AplicacionesIngenieria/venv/bin/python app_presupuesto_filtro.py --resumen --sync-ods
```

---

## 4. Resumen Base del Presupuesto y Mano de Obra ($L_{filtro}=30\text{ ml}$, $L_{ronda}=40\text{ ml}$)

- **Subtotal Capítulo I (Filtro Francés - 30 ml)**: `$5,691,885.27 COP`
- **Subtotal Capítulo II (Ronda de Coronación - 40 ml)**: `$4,241,946.40 COP`
- **Costo Directo Total**: **`$9,933,831.67 COP`**
- **VALOR TOTAL DE LA MANO DE OBRA DIRECTA**: **`$3,033,224.00 COP`** (`30.53%` del Costo Directo)
  - **Oficial de Obra** (`$120,000/día`): `9.98 jornales` $\rightarrow$ `$1,197,440.00 COP`
  - **Obrero / Ayudante** (`$90,000/día`): `20.40 jornales` $\rightarrow$ `$1,835,784.00 COP`
  - **Total Jornales Hombre-Día**: `30.38 jornales` (~`11 días hábiles` con cuadrilla de 1 Oficial + 2 Ayudantes)
- **Total A.I.U. (20%: Admin 10%, Imprevistos 5%, Utilidad 5%)**: **`$1,986,766.33 COP`**
- **VALOR TOTAL DEL CONTRATO**: **`$11,920,598.01 COP`**
