#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_presupuesto_filtro.py
===============================================================================
SISTEMA DE INGENIERÍA, PRESUPUESTO APU Y CONTROL DE COSTOS — CONTROL DE INUNDACIÓN
Proyecto: Filtro Francés (Subdrenaje) + Ronda / Cuneta de Coronación en Concreto
Ubicación: Sector Rural — Oriente Antioqueño

Desarrollado para: Ing. Oscar Fernando Valencia
Basado exactamente en:
  - Presupuesto Filtro.ods (01_PRESUPUESTO, 02_APU, 03_INSUMOS)
  - Presentación Filtro.odp (Diagnóstico, Diseño Técnico y Propuesta Económica)

Funcionalidades principales:
  1. Visualización destacada del VALOR TOTAL DE LA MANO DE OBRA (consolidado,
     por cuadrilla Oficial vs. Ayudante, total de jornales requeridos y desglose
     por cada una de las 12 actividades del presupuesto).
  2. Modificación interactiva del precio unitario de cualquiera de los 23 insumos
     con recálculo instantáneo de todos los APUs, valores unitarios, totales por
     actividad, costos directos, AIU y valor total del contrato.
  3. Modificación paramétrica de las dimensiones geométricas del proyecto
     (Longitud del Filtro Francés L_filtro, ancho/profundidad de zanja, altura
     de grava; Longitud de la Ronda de Coronación L_ronda y espesor e) con
     actualización automática de cantidades de obra.
  4. Explosión consolidada de insumos / Lista de compras en unidades comerciales
     (bultos de cemento, m³ de grava/arena/triturado, m² de geotextil/malla, etc.).
  5. Simulador de escenarios y contingencia para negociación en visita técnica.
  6. Sincronización directa con el archivo 'Presupuesto Filtro.ods' (actualiza
     precios de insumos y longitudes en las hojas de cálculo de LibreOffice) y
     exportación de reportes técnicos en Markdown/CSV/JSON.
===============================================================================
"""

import os
import sys
import json
import math
import shutil
import zipfile
import argparse
import datetime
import xml.etree.ElementTree as ET
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ODS_PATH = os.path.join(BASE_DIR, "Presupuesto Filtro.ods")
JSON_PATH = os.path.join(BASE_DIR, "datos_presupuesto.json")
REPORTE_MD_PATH = os.path.join(BASE_DIR, "Reporte_Presupuesto_y_Mano_de_Obra.md")


# =============================================================================
# 1. BASE DE DATOS INICIAL (EXACTA DE 'Presupuesto Filtro.ods' y '.odp')
# =============================================================================
DEFAULT_STATE = {
    "proyecto": {
        "nombre": "Construcción de Filtro Francés y Ronda de Coronación — Control de Inundación",
        "ubicacion": "Predio Rural — Municipio del Oriente Antioqueño",
        "fecha_programada": "Noviembre 2026",
        "ingeniero": "Ing. Oscar Fernando Valencia",
        "aiu_administracion_pct": 10.0,
        "aiu_imprevistos_pct": 5.0,
        "aiu_utilidad_pct": 5.0
    },
    "geometria": {
        # Capítulo I: Filtro Francés
        "L_filtro_ml": 30.0,
        "area_preliminares_m2": 20.0,
        "ancho_zanja_filtro_m": 0.40,
        "prof_zanja_filtro_m": 0.80,
        "altura_grava_filtro_m": 0.60,
        "altura_cierre_filtro_m": 0.20,
        # Capítulo II: Ronda de Coronación
        "L_ronda_ml": 40.0,
        "b_menor_exc_ronda_m": 0.45,
        "b_mayor_exc_ronda_m": 0.65,
        "h_exc_ronda_m": 0.40,
        "talud_int_ronda_m": 0.41,
        "base_int_ronda_m": 0.30,
        "espesor_concreto_ronda_m": 0.075
    },
    "insumos": {
        "2":  {"codigo": 2,  "nombre": "Pisón manual apisonador de grava y zanja",                   "unidad": "día",      "precio": 25000.0,  "precio_base": 25000.0,  "categoria": "Equipos"},
        "3":  {"codigo": 3,  "nombre": "Equipo básico de nivelación y pendientes",                   "unidad": "día",      "precio": 15000.0,  "precio_base": 15000.0,  "categoria": "Equipos"},
        "4":  {"codigo": 4,  "nombre": "Carretilla tipo buggi para acarreo",                         "unidad": "día",      "precio": 18000.0,  "precio_base": 18000.0,  "categoria": "Equipos"},
        "5":  {"codigo": 5,  "nombre": "Obrero / Ayudante de construcción",                          "unidad": "día",      "precio": 90000.0,  "precio_base": 90000.0,  "categoria": "Mano de obra"},
        "6":  {"codigo": 6,  "nombre": "Oficial de obra (trazo, niveles, geotextil y tubería)",      "unidad": "día",      "precio": 120000.0, "precio_base": 120000.0, "categoria": "Mano de obra"},
        "7":  {"codigo": 7,  "nombre": "Flete de grava triturada en volqueta hasta predio",          "unidad": "m³",       "precio": 50000.0,  "precio_base": 50000.0,  "categoria": "Transporte"},
        "8":  {"codigo": 8,  "nombre": "Acarreo interno manual de grava a zanja",                    "unidad": "m³",       "precio": 16000.0,  "precio_base": 16000.0,  "categoria": "Transporte"},
        "9":  {"codigo": 9,  "nombre": "Flete proporcional materiales livianos (tubería y geotextil)", "unidad": "ml",     "precio": 1900.0,   "precio_base": 1900.0,   "categoria": "Transporte"},
        "10": {"codigo": 10, "nombre": "Geotextil no tejido NT 1600 / NT 1800 (polipropileno)",      "unidad": "m²",       "precio": 5800.0,   "precio_base": 5800.0,   "categoria": "Materiales"},
        "11": {"codigo": 11, "nombre": "Tubería corrugada de drenaje perforada 4\" (HDPE/PVC)",      "unidad": "m",        "precio": 15000.0,  "precio_base": 15000.0,  "categoria": "Materiales"},
        "12": {"codigo": 12, "nombre": "Grava filtrante triturada limpia (3/4\" a 1-1/2\")",         "unidad": "m³",       "precio": 250000.0, "precio_base": 250000.0, "categoria": "Materiales"},
        "13": {"codigo": 13, "nombre": "Arena gruesa limpia de lecho / asiento de filtro",           "unidad": "m³",       "precio": 210000.0, "precio_base": 210000.0, "categoria": "Materiales"},
        "14": {"codigo": 14, "nombre": "Accesorios de conexión 4\" (uniones, codos, terminal)",      "unidad": "und",      "precio": 12500.0,  "precio_base": 12500.0,  "categoria": "Materiales"},
        "15": {"codigo": 15, "nombre": "Alambre negro de amarre No. 18 / grapas de sujeción",        "unidad": "kg",       "precio": 8500.0,   "precio_base": 8500.0,   "categoria": "Materiales"},
        "16": {"codigo": 16, "nombre": "Cinta de señalización de peligro (rollo 500 m)",             "unidad": "und",      "precio": 30000.0,  "precio_base": 30000.0,  "categoria": "Materiales"},
        "17": {"codigo": 17, "nombre": "Cemento gris tipo Portland (saco 50 kg)",                    "unidad": "bulto",    "precio": 36000.0,  "precio_base": 36000.0,  "categoria": "Materiales"},
        "18": {"codigo": 18, "nombre": "Arena lavada para concreto/mortero",                         "unidad": "m³",       "precio": 150000.0, "precio_base": 150000.0, "categoria": "Materiales"},
        "19": {"codigo": 19, "nombre": "Triturado 1/2\" para concreto",                              "unidad": "m³",       "precio": 200000.0, "precio_base": 200000.0, "categoria": "Materiales"},
        "20": {"codigo": 20, "nombre": "Malla electrosoldada M-084 / Q-106 (alambre 4.0 mm)",        "unidad": "m²",       "precio": 9500.0,   "precio_base": 9500.0,   "categoria": "Materiales"},
        "21": {"codigo": 21, "nombre": "Aditivo impermeabilizante integral líquido (Sika 1)",        "unidad": "kg",       "precio": 9500.0,   "precio_base": 9500.0,   "categoria": "Materiales"},
        "22": {"codigo": 22, "nombre": "Sellante elástico para juntas de dilatación",                "unidad": "cartucho", "precio": 28000.0,  "precio_base": 28000.0,  "categoria": "Materiales"},
        "23": {"codigo": 23, "nombre": "Membrana / aditivo de curado para concreto",                 "unidad": "galón",    "precio": 32000.0,  "precio_base": 32000.0,  "categoria": "Materiales"},
        "24": {"codigo": 24, "nombre": "Mezcladora de concreto (trompo 1 bulto)",                    "unidad": "día",      "precio": 65000.0,  "precio_base": 65000.0,  "categoria": "Equipos"}
    }
}


# =============================================================================
# 2. MOTOR MATEMÁTICO DE PRESUPUESTO, APUs, MANO DE OBRA Y EXPLOSIÓN DE INSUMOS
# =============================================================================
class MotorPresupuestoFiltro:
    """
    Motor de cálculo exacto sincronizado con las fórmulas de 'Presupuesto Filtro.ods'.
    """

    def __init__(self, ruta_json: str = JSON_PATH):
        self.ruta_json = ruta_json
        self.datos = deepcopy(DEFAULT_STATE)
        self.cargar_datos()

    def cargar_datos(self):
        if os.path.exists(self.ruta_json):
            try:
                with open(self.ruta_json, "r", encoding="utf-8") as f:
                    cargado = json.load(f)
                for k in ["proyecto", "geometria", "insumos"]:
                    if k in cargado:
                        self.datos[k].update(cargado[k])
            except Exception as e:
                print(f"Aviso: No se pudo cargar {self.ruta_json}, usando valores por defecto ({e}).")
        else:
            self.guardar_datos()

    def guardar_datos(self):
        with open(self.ruta_json, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)

    def restaurar_valores_originales(self):
        self.datos = deepcopy(DEFAULT_STATE)
        self.guardar_datos()

    def P(self, cod: int) -> float:
        """Retorna el precio unitario actual del insumo con código `cod`."""
        return float(self.datos["insumos"][str(cod)]["precio"])

    def definir_actividades_apu(self) -> list:
        """
        Construye y evalúa las 12 actividades del presupuesto con la estructura exacta
        de la hoja 02_APU y 01_PRESUPUESTO de 'Presupuesto Filtro.ods'.
        """
        g = self.datos["geometria"]
        Lf = float(g["L_filtro_ml"])
        W = float(g["ancho_zanja_filtro_m"])
        H = float(g["prof_zanja_filtro_m"])
        hg = float(g["altura_grava_filtro_m"])
        hc = float(g["altura_cierre_filtro_m"])

        Lr = float(g["L_ronda_ml"])
        b_men = float(g["b_menor_exc_ronda_m"])
        b_may = float(g["b_mayor_exc_ronda_m"])
        h_exc = float(g["h_exc_ronda_m"])
        t_int = float(g["talud_int_ronda_m"])
        b_int = float(g["base_int_ronda_m"])
        e_conc = float(g["espesor_concreto_ronda_m"])

        # Cantidades de obra según geometría (exactamente igual a 01_PRESUPUESTO)
        q_item1 = float(g["area_preliminares_m2"])
        q_item2 = H * W * Lf                                    # 0.8 * 0.4 * 30 = 9.60 m³
        q_item3 = Lf                                            # 30.0 ml
        q_item4 = hg * W * Lf                                   # 0.6 * 0.4 * 30 = 7.20 m³
        q_item5 = Lf                                            # 30.0 ml

        q_item6 = Lr                                            # 40.0 ml
        q_item7 = ((b_men + b_may) * h_exc / 2.0) * Lr          # (0.45+0.65)*0.4/2 * 40 = 8.80 m³
        q_item8 = Lr                                            # 40.0 ml
        q_item9 = (t_int + t_int + b_int) * 1.0 * Lr            # (0.41+0.41+0.30)*1 * 40 = 44.80 m²
        q_item10 = (2.0 * t_int * e_conc + b_int * e_conc) * Lr # (2*0.41*0.075 + 0.3*0.075)*40 = 3.36 m³
        q_item11 = Lr                                           # 40.0 ml
        q_item12 = Lr                                           # 40.0 ml

        # Definición detallada de cada ítem con sus componentes APU:
        # Cada línea de insumo es: (codigo_insumo, rendimiento_por_unidad)
        raw_items = [
            # ==================== CAPÍTULO I: FILTRO FRANCÉS ====================
            {
                "item": 1,
                "capitulo": "I",
                "capitulo_nombre": "CAPÍTULO I: CONSTRUCCIÓN DE FILTRO FRANCÉS (SUBDRENAJE)",
                "nombre": "PRELIMINARES Y TRAZADO CON PENDIENTES",
                "unidad": "m²",
                "cantidad": q_item1,
                "formula_cantidad": f"Área fija = {q_item1:.2f} m²",
                "pct_herramienta_menor": 0.05,
                "equipos": [(3, 0.02), (4, 0.03)],
                "materiales": [],
                "transporte": [],
                "mano_de_obra": [(6, 1.0 / 30.0), (5, 1.0 / 40.0)]
            },
            {
                "item": 2,
                "capitulo": "I",
                "capitulo_nombre": "CAPÍTULO I: CONSTRUCCIÓN DE FILTRO FRANCÉS (SUBDRENAJE)",
                "nombre": "MOVIMIENTO DE TIERRAS (EXCAVACIÓN MANUAL DE ZANJA)",
                "unidad": "m³",
                "cantidad": q_item2,
                "formula_cantidad": f"{H:.2f}m × {W:.2f}m × {Lf:.1f}ml = {q_item2:.2f} m³",
                "pct_herramienta_menor": 0.10,
                "equipos": [(3, 0.02), (4, 0.03)],
                "materiales": [],
                "transporte": [],
                "mano_de_obra": [(6, 1.0 / 6.0), (5, 1.0 / 4.0)]
            },
            {
                "item": 3,
                "capitulo": "I",
                "capitulo_nombre": "CAPÍTULO I: CONSTRUCCIÓN DE FILTRO FRANCÉS (SUBDRENAJE)",
                "nombre": "GEOSINTÉTICOS Y TUBERÍA DE DRENAJE 4\" PERFORADA",
                "unidad": "ml",
                "cantidad": q_item3,
                "formula_cantidad": f"L_filtro = {Lf:.2f} ml",
                "pct_herramienta_menor": 0.05,
                "equipos": [(3, 0.02)],
                "materiales": [
                    (10, (W + 2.0 * H + 0.70) * 1.07),  # (0.4+2*0.8+0.7)*1.07 = 2.889 m²/ml
                    (11, 1.05),
                    (14, 0.07),
                    (15, 0.05)
                ],
                "transporte": [(9, 1.00)],
                "mano_de_obra": [(6, 1.0 / 50.0), (5, 1.0 / 25.0)]
            },
            {
                "item": 4,
                "capitulo": "I",
                "capitulo_nombre": "CAPÍTULO I: CONSTRUCCIÓN DE FILTRO FRANCÉS (SUBDRENAJE)",
                "nombre": "ESTRUCTURA FILTRANTE (GRAVA LIMPIA, FLETE Y ACARREOS)",
                "unidad": "m³",
                "cantidad": q_item4,
                "formula_cantidad": f"{hg:.2f}m × {W:.2f}m × {Lf:.1f}ml = {q_item4:.2f} m³",
                "pct_herramienta_menor": 0.10,
                "equipos": [(2, 1.0 / 20.0), (3, 1.0 / 40.0), (4, 1.0 / 33.0)],
                "materiales": [(12, 1.00)],
                "transporte": [(7, 1.00), (8, 1.00)],
                "mano_de_obra": [(6, 0.125), (5, 0.40)]
            },
            {
                "item": 5,
                "capitulo": "I",
                "capitulo_nombre": "CAPÍTULO I: CONSTRUCCIÓN DE FILTRO FRANCÉS (SUBDRENAJE)",
                "nombre": "CIERRE, TRASLAPO, PROTECCIÓN Y MANEJO DE SOBRANTES",
                "unidad": "ml",
                "cantidad": q_item5,
                "formula_cantidad": f"L_filtro = {Lf:.2f} ml",
                "pct_herramienta_menor": 0.10,
                "equipos": [(2, 0.025), (3, 0.02), (4, 0.03)],
                "materiales": [(12, hc * W * 1.07)],  # 0.2*0.4*1.07 = 0.0856 m³/ml
                "transporte": [(8, hc * W * 1.07)],   # 0.0856 m³/ml
                "mano_de_obra": [(6, 1.0 / 20.0), (5, 1.0 / 15.0)]
            },
            # ==================== CAPÍTULO II: RONDA DE CORONACIÓN ====================
            {
                "item": 6,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "LOCALIZACIÓN, TRAZADO Y REPLANTEO DE CUNETA EN LADERA",
                "unidad": "ml",
                "cantidad": q_item6,
                "formula_cantidad": f"L_ronda = {Lr:.2f} ml",
                "pct_herramienta_menor": 0.10,
                "equipos": [(3, 0.02)],
                "materiales": [],
                "transporte": [],
                "mano_de_obra": [(6, 0.033), (5, 0.025)]
            },
            {
                "item": 7,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "DESCAPOTE Y EXCAVACIÓN MANUAL DE ZANJA TRAPEZOIDAL",
                "unidad": "m³",
                "cantidad": q_item7,
                "formula_cantidad": f"(({b_men:.2f}+{b_may:.2f})×{h_exc:.2f}/2)×{Lr:.1f}ml = {q_item7:.2f} m³",
                "pct_herramienta_menor": 0.10,
                "equipos": [],
                "materiales": [],
                "transporte": [],
                "mano_de_obra": [(6, 0.04), (5, 0.35)]
            },
            {
                "item": 8,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "CONFORMACIÓN, PERFILADO Y COMPACTACIÓN DE CAJA",
                "unidad": "ml",
                "cantidad": q_item8,
                "formula_cantidad": f"L_ronda = {Lr:.2f} ml",
                "pct_herramienta_menor": 0.0,
                "equipos": [(2, 0.025)],
                "materiales": [],
                "transporte": [],
                "mano_de_obra": [(6, 0.006), (5, 0.035)]
            },
            {
                "item": 9,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "SUMINISTRO Y COLOCACIÓN DE MALLA ELECTROSOLDADA M-084",
                "unidad": "m²",
                "cantidad": q_item9,
                "formula_cantidad": f"(2×{t_int:.2f}+{b_int:.2f})×{Lr:.1f}ml = {q_item9:.2f} m²",
                "pct_herramienta_menor": 0.10,
                "equipos": [],
                "materiales": [(20, 1.10), (15, 0.05)],
                "transporte": [],
                "mano_de_obra": [(6, 0.015), (5, 0.022)]
            },
            {
                "item": 10,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "SUMINISTRO, TRANSPORTE Y VACIADO DE CONCRETO 2500 PSI (e=7.5 cm)",
                "unidad": "m³",
                "cantidad": q_item10,
                "formula_cantidad": f"(2×{t_int:.2f}+{b_int:.2f})×{e_conc:.3f}m×{Lr:.1f}ml = {q_item10:.2f} m³",
                "pct_herramienta_menor": 0.05,
                "equipos": [(24, 0.08)],
                "materiales": [(17, 7.50), (18, 0.55), (19, 0.85), (21, 4.00)],
                "transporte": [],
                "mano_de_obra": [(6, 0.30), (5, 0.70)]
            },
            {
                "item": 11,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "AFINADO LISO, JUNTAS DE DILATACIÓN Y CURADO",
                "unidad": "ml",
                "cantidad": q_item11,
                "formula_cantidad": f"L_ronda = {Lr:.2f} ml",
                "pct_herramienta_menor": 0.05,
                "equipos": [],
                "materiales": [(22, 0.08), (23, 0.02)],
                "transporte": [],
                "mano_de_obra": [(6, 0.025), (5, 0.015)]
            },
            {
                "item": 12,
                "capitulo": "II",
                "capitulo_nombre": "CAPÍTULO II: CONSTRUCCIÓN DE RONDA O CUNETA DE CORONACIÓN",
                "nombre": "CONFORMACIÓN DE CABALLÓN DE TIERRA Y MANEJO DE SOBRANTES",
                "unidad": "ml",
                "cantidad": q_item12,
                "formula_cantidad": f"L_ronda = {Lr:.2f} ml",
                "pct_herramienta_menor": 0.05,
                "equipos": [],
                "materiales": [],
                "transporte": [],
                "mano_de_obra": [(6, 0.003), (5, 0.050)]
            }
        ]

        actividades_calculadas = []
        for act in raw_items:
            cant = act["cantidad"]

            # 1. Mano de obra unitaria
            mo_unit = 0.0
            jornales_oficial_unit = 0.0
            jornales_ayudante_unit = 0.0
            costo_oficial_unit = 0.0
            costo_ayudante_unit = 0.0
            detalle_mo = []
            for cod, rend in act["mano_de_obra"]:
                p_ins = self.P(cod)
                sub = rend * p_ins
                mo_unit += sub
                if cod == 6:
                    jornales_oficial_unit += rend
                    costo_oficial_unit += sub
                elif cod == 5:
                    jornales_ayudante_unit += rend
                    costo_ayudante_unit += sub
                detalle_mo.append({
                    "codigo": cod,
                    "nombre": self.datos["insumos"][str(cod)]["nombre"],
                    "unidad": self.datos["insumos"][str(cod)]["unidad"],
                    "rendimiento": rend,
                    "precio_unitario": p_ins,
                    "subtotal_unitario": sub,
                    "cantidad_total_obra": rend * cant,
                    "costo_total_obra": sub * cant
                })

            # 2. Equipos unitarios (incluyendo Herramienta Menor = % de MO)
            herr_menor_unit = act["pct_herramienta_menor"] * mo_unit
            eq_unit = herr_menor_unit
            detalle_eq = []
            if act["pct_herramienta_menor"] > 0:
                detalle_eq.append({
                    "codigo": 0,
                    "nombre": f"Herramienta menor ({int(act['pct_herramienta_menor']*100)}% M.O.)",
                    "unidad": "% MO",
                    "rendimiento": act["pct_herramienta_menor"],
                    "precio_unitario": mo_unit,
                    "subtotal_unitario": herr_menor_unit,
                    "cantidad_total_obra": act["pct_herramienta_menor"],
                    "costo_total_obra": herr_menor_unit * cant
                })
            for cod, rend in act["equipos"]:
                p_ins = self.P(cod)
                sub = rend * p_ins
                eq_unit += sub
                detalle_eq.append({
                    "codigo": cod,
                    "nombre": self.datos["insumos"][str(cod)]["nombre"],
                    "unidad": self.datos["insumos"][str(cod)]["unidad"],
                    "rendimiento": rend,
                    "precio_unitario": p_ins,
                    "subtotal_unitario": sub,
                    "cantidad_total_obra": rend * cant,
                    "costo_total_obra": sub * cant
                })

            # 3. Materiales unitarios
            mat_unit = 0.0
            detalle_mat = []
            for cod, rend in act["materiales"]:
                p_ins = self.P(cod)
                sub = rend * p_ins
                mat_unit += sub
                detalle_mat.append({
                    "codigo": cod,
                    "nombre": self.datos["insumos"][str(cod)]["nombre"],
                    "unidad": self.datos["insumos"][str(cod)]["unidad"],
                    "rendimiento": rend,
                    "precio_unitario": p_ins,
                    "subtotal_unitario": sub,
                    "cantidad_total_obra": rend * cant,
                    "costo_total_obra": sub * cant
                })

            # 4. Transporte unitario
            trans_unit = 0.0
            detalle_trans = []
            for cod, rend in act["transporte"]:
                p_ins = self.P(cod)
                sub = rend * p_ins
                trans_unit += sub
                detalle_trans.append({
                    "codigo": cod,
                    "nombre": self.datos["insumos"][str(cod)]["nombre"],
                    "unidad": self.datos["insumos"][str(cod)]["unidad"],
                    "rendimiento": rend,
                    "precio_unitario": p_ins,
                    "subtotal_unitario": sub,
                    "cantidad_total_obra": rend * cant,
                    "costo_total_obra": sub * cant
                })

            vr_unitario = eq_unit + mat_unit + trans_unit + mo_unit
            vr_total = vr_unitario * cant

            actividades_calculadas.append({
                **act,
                "eq_unit": eq_unit,
                "mat_unit": mat_unit,
                "trans_unit": trans_unit,
                "mo_unit": mo_unit,
                "vr_unitario": vr_unitario,
                "vr_total": vr_total,
                "eq_total": eq_unit * cant,
                "mat_total": mat_unit * cant,
                "trans_total": trans_unit * cant,
                "mo_total": mo_unit * cant,
                "jornales_oficial_total": jornales_oficial_unit * cant,
                "jornales_ayudante_total": jornales_ayudante_unit * cant,
                "costo_oficial_total": costo_oficial_unit * cant,
                "costo_ayudante_total": costo_ayudante_unit * cant,
                "detalle_eq": detalle_eq,
                "detalle_mat": detalle_mat,
                "detalle_trans": detalle_trans,
                "detalle_mo": detalle_mo
            })

        return actividades_calculadas

    def calcular_resumen_general(self) -> dict:
        """
        Retorna todos los totales del presupuesto, desglose por capítulos,
        valor total de la mano de obra (Oficial + Ayudante + jornales),
        y explosión consolidada de insumos.
        """
        actividades = self.definir_actividades_apu()

        cap1_acts = [a for a in actividades if a["capitulo"] == "I"]
        cap2_acts = [a for a in actividades if a["capitulo"] == "II"]

        sub_cap1 = sum(a["vr_total"] for a in cap1_acts)
        sub_cap2 = sum(a["vr_total"] for a in cap2_acts)
        costo_directo = sub_cap1 + sub_cap2

        # Totales por categoría de costo directo
        total_equipos = sum(a["eq_total"] for a in actividades)
        total_materiales = sum(a["mat_total"] for a in actividades)
        total_transporte = sum(a["trans_total"] for a in actividades)
        total_mano_de_obra = sum(a["mo_total"] for a in actividades)

        # Desglose de Mano de Obra
        mo_cap1 = sum(a["mo_total"] for a in cap1_acts)
        mo_cap2 = sum(a["mo_total"] for a in cap2_acts)
        jornales_oficial = sum(a["jornales_oficial_total"] for a in actividades)
        jornales_ayudante = sum(a["jornales_ayudante_total"] for a in actividades)
        costo_oficial = sum(a["costo_oficial_total"] for a in actividades)
        costo_ayudante = sum(a["costo_ayudante_total"] for a in actividades)

        # AIU y Total Contrato
        p = self.datos["proyecto"]
        pct_adm = float(p["aiu_administracion_pct"]) / 100.0
        pct_imp = float(p["aiu_imprevistos_pct"]) / 100.0
        pct_uti = float(p["aiu_utilidad_pct"]) / 100.0
        pct_aiu = pct_adm + pct_imp + pct_uti

        vr_adm = costo_directo * pct_adm
        vr_imp = costo_directo * pct_imp
        vr_uti = costo_directo * pct_uti
        vr_aiu = costo_directo * pct_aiu
        vr_total_contrato = costo_directo + vr_aiu

        # Explosión consolidada de insumos (Cantidades totales requeridas en toda la obra)
        explosion = {}
        for k, ins in self.datos["insumos"].items():
            cod = ins["codigo"]
            explosion[cod] = {
                "codigo": cod,
                "nombre": ins["nombre"],
                "unidad": ins["unidad"],
                "categoria": ins["categoria"],
                "precio_unitario": float(ins["precio"]),
                "precio_base": float(ins["precio_base"]),
                "cantidad_total": 0.0,
                "costo_total": 0.0,
                "actividades_uso": []
            }

        for a in actividades:
            for lista_det in [a["detalle_eq"], a["detalle_mat"], a["detalle_trans"], a["detalle_mo"]]:
                for det in lista_det:
                    cod = det["codigo"]
                    if cod in explosion:
                        explosion[cod]["cantidad_total"] += det["cantidad_total_obra"]
                        explosion[cod]["costo_total"] += det["costo_total_obra"]
                        explosion[cod]["actividades_uso"].append(f"Ítem {a['item']}")

        # Redondeo comercial sugerido para compras
        for cod, exp in explosion.items():
            cant_exacta = exp["cantidad_total"]
            if cant_exacta > 0:
                if exp["unidad"] in ["bulto", "und", "cartucho", "galón", "kg"]:
                    exp["cantidad_comercial_sugerida"] = math.ceil(cant_exacta)
                elif exp["unidad"] in ["día"]:
                    exp["cantidad_comercial_sugerida"] = round(cant_exacta, 1)
                else:
                    exp["cantidad_comercial_sugerida"] = round(cant_exacta, 2)
            else:
                exp["cantidad_comercial_sugerida"] = 0

        return {
            "actividades": actividades,
            "subtotal_cap1": sub_cap1,
            "subtotal_cap2": sub_cap2,
            "costo_directo": costo_directo,
            "total_equipos": total_equipos,
            "total_materiales": total_materiales,
            "total_transporte": total_transporte,
            "total_mano_de_obra": total_mano_de_obra,
            "mo_cap1": mo_cap1,
            "mo_cap2": mo_cap2,
            "jornales_oficial": jornales_oficial,
            "jornales_ayudante": jornales_ayudante,
            "jornales_totales": jornales_oficial + jornales_ayudante,
            "costo_oficial": costo_oficial,
            "costo_ayudante": costo_ayudante,
            "pct_aiu_total": pct_aiu * 100.0,
            "vr_administracion": vr_adm,
            "vr_imprevistos": vr_imp,
            "vr_utilidad": vr_uti,
            "vr_aiu": vr_aiu,
            "vr_total_contrato": vr_total_contrato,
            "explosion_insumos": explosion
        }

    # =========================================================================
    # 3. SINCRONIZACIÓN DIRECTA CON 'Presupuesto Filtro.ods'
    # =========================================================================
    def sincronizar_archivo_ods(self, ruta_ods: str = ODS_PATH) -> tuple[bool, str]:
        """
        Actualiza directamente el archivo OpenDocument Spreadsheet (.ods):
          1. Actualiza los precios unitarios de los 23 insumos en la hoja '03_INSUMOS'.
          2. Actualiza las longitudes base L_filtro (celda D9) y L_ronda (celda D18)
             y las cantidades/totales precalculados en '01_PRESUPUESTO' y '02_APU'.
        """
        if not os.path.exists(ruta_ods):
            return False, f"No se encontró el archivo ODS en: {ruta_ods}"

        try:
            resumen = self.calcular_resumen_general()
            acts_by_item = {a["item"]: a for a in resumen["actividades"]}
            Lf = float(self.datos["geometria"]["L_filtro_ml"])
            Lr = float(self.datos["geometria"]["L_ronda_ml"])

            # Leer archivo zip (.ods)
            with zipfile.ZipFile(ruta_ods, "r") as zin:
                namelist = zin.namelist()
                files_content = {name: zin.read(name) for name in namelist}

            ET.register_namespace("office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0")
            ET.register_namespace("table", "urn:oasis:names:tc:opendocument:xmlns:table:1.0")
            ET.register_namespace("text", "urn:oasis:names:tc:opendocument:xmlns:text:1.0")
            ET.register_namespace("calcext", "urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0")

            root = ET.fromstring(files_content["content.xml"])
            ns = {
                "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
                "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
                "text": "urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0",
                "t": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
            }

            def set_cell_float(cell, val: float, fmt_currency: bool = True):
                cell.set("{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value-type", "float")
                cell.set("{urn:oasis:names:tc:opendocument:xmlns:office:1.0}value", f"{val:.4f}".rstrip("0").rstrip(".") if val % 1 != 0 else str(int(val)))
                p_elem = cell.find("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p")
                if p_elem is None:
                    p_elem = ET.SubElement(cell, "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p")
                if fmt_currency:
                    p_elem.text = f"${val:,.2f}"
                else:
                    p_elem.text = f"{val:,.2f}"

            def expand_row_cells(row):
                """Expande celdas con number-columns-repeated para poder editar por índice de columna."""
                new_cells = []
                for c in list(row):
                    rep = int(c.get("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated", "1"))
                    if rep > 1 and len(new_cells) < 12:
                        c.attrib.pop("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated", None)
                        for _ in range(rep):
                            new_cells.append(deepcopy(c))
                    else:
                        new_cells.append(c)
                row[:] = new_cells
                return new_cells

            for sheet in root.findall(".//table:table", ns):
                sheet_name = sheet.get("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}name")
                rows = sheet.findall("table:table-row", ns)

                # 1. Hoja 03_INSUMOS: filas 2 a 24 (índices 1 a 23) contienen códigos 2 a 24
                if sheet_name == "03_INSUMOS":
                    for r_idx in range(1, min(24, len(rows))):
                        cells = expand_row_cells(rows[r_idx])
                        if len(cells) >= 4:
                            cod_str = str(r_idx + 1)
                            if cod_str in self.datos["insumos"]:
                                nuevo_precio = float(self.datos["insumos"][cod_str]["precio"])
                                set_cell_float(cells[3], nuevo_precio, fmt_currency=True)

                # 2. Hoja 01_PRESUPUESTO: actualizar cantidades, valores unitarios y totales cacheados
                elif sheet_name == "01_PRESUPUESTO":
                    # Mapa de fila (1-indexed en Calc -> 0-indexed en lista) para cada ítem
                    item_row_map = {
                        1: 6,   # Row 7
                        2: 7,   # Row 8
                        3: 8,   # Row 9 (contiene L_filtro en col D)
                        4: 9,   # Row 10
                        5: 10,  # Row 11
                        6: 15,  # Row 16
                        7: 16,  # Row 17
                        8: 17,  # Row 18 (contiene L_ronda en col D)
                        9: 18,  # Row 19
                        10: 19, # Row 20
                        11: 20, # Row 21
                        12: 21  # Row 22
                    }
                    for item_num, r_idx in item_row_map.items():
                        if r_idx < len(rows):
                            cells = expand_row_cells(rows[r_idx])
                            act = acts_by_item[item_num]
                            # Col D (idx 3) = Cantidad, Col E (idx 4) = Vr Unitario, Col F (idx 5) = Vr Total
                            if len(cells) >= 6:
                                set_cell_float(cells[3], act["cantidad"], fmt_currency=False)
                                set_cell_float(cells[4], act["vr_unitario"], fmt_currency=True)
                                set_cell_float(cells[5], act["vr_total"], fmt_currency=True)

                    # Subtotales y Totales en 01_PRESUPUESTO
                    totales_row_map = [
                        (11, resumen["subtotal_cap1"]),     # Row 12: Subtotal Cap I
                        (22, resumen["subtotal_cap2"]),     # Row 23: Subtotal Cap II
                        (24, resumen["costo_directo"]),     # Row 25: Costo Directo
                        (25, resumen["vr_aiu"]),            # Row 26: AIU
                        (26, resumen["vr_total_contrato"])  # Row 27: Valor Total
                    ]
                    for r_idx, val in totales_row_map:
                        if r_idx < len(rows):
                            cells = expand_row_cells(rows[r_idx])
                            if len(cells) >= 6:
                                set_cell_float(cells[5], val, fmt_currency=True)

            files_content["content.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

            with zipfile.ZipFile(ruta_ods, "w", zipfile.ZIP_DEFLATED) as zout:
                # 'mimetype' debe ir primero y sin comprimir según estándar ODF
                if "mimetype" in files_content:
                    zout.writestr("mimetype", files_content["mimetype"], compress_type=zipfile.ZIP_STORED)
                for name, content in files_content.items():
                    if name != "mimetype":
                        zout.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)

            return True, f"Archivo '{os.path.basename(ruta_ods)}' sincronizado exitosamente."
        except Exception as e:
            return False, f"Error al sincronizar archivo ODS: {e}"

    def generar_reporte_markdown(self, ruta_md: str = REPORTE_MD_PATH) -> str:
        """Genera un informe ejecutivo y técnico completo en Markdown."""
        res = self.calcular_resumen_general()
        g = self.datos["geometria"]
        p = self.datos["proyecto"]

        lineas = [
            f"# 📊 Reporte Técnico, Presupuesto APU y Mano de Obra — {p['nombre']}",
            f"**Ubicación:** {p['ubicacion']} | **Fecha programada:** {p['fecha_programada']} | **Responsable:** {p['ingeniero']}",
            "",
            "---",
            "",
            "## 1. Resumen Financiero Ejecutivo",
            "",
            "| Concepto | Valor (COP) | Participación (%) |",
            "| :--- | ---: | ---: |",
            f"| **Subtotal Capítulo I: Filtro Francés ({g['L_filtro_ml']:.1f} ml)** | **${res['subtotal_cap1']:,.2f}** | {(res['subtotal_cap1']/res['costo_directo']*100):.1f}% del C.D. |",
            f"| **Subtotal Capítulo II: Ronda de Coronación ({g['L_ronda_ml']:.1f} ml)** | **${res['subtotal_cap2']:,.2f}** | {(res['subtotal_cap2']/res['costo_directo']*100):.1f}% del C.D. |",
            f"| **COSTO DIRECTO TOTAL DE OBRA** | **${res['costo_directo']:,.2f}** | **100.0% C.D.** |",
            f"| Administración ({p['aiu_administracion_pct']:.1f}%) | ${res['vr_administracion']:,.2f} | - |",
            f"| Imprevistos ({p['aiu_imprevistos_pct']:.1f}%) | ${res['vr_imprevistos']:,.2f} | - |",
            f"| Utilidad ({p['aiu_utilidad_pct']:.1f}%) | ${res['vr_utilidad']:,.2f} | - |",
            f"| **Total A.I.U. ({res['pct_aiu_total']:.1f}%)** | **${res['vr_aiu']:,.2f}** | - |",
            f"| **VALOR TOTAL DEL CONTRATO (CON AIU)** | **${res['vr_total_contrato']:,.2f}** | **Total Propuesta** |",
            "",
            "---",
            "",
            "## 2. Desglose del Valor Total de la Mano de Obra",
            "",
            f"- **VALOR TOTAL MANO DE OBRA DIRECTA:** **${res['total_mano_de_obra']:,.2f} COP** ({(res['total_mano_de_obra']/res['costo_directo']*100):.1f}% del Costo Directo)",
            f"  - **Mano de Obra Capítulo I (Filtro Francés):** ${res['mo_cap1']:,.2f} COP",
            f"  - **Mano de Obra Capítulo II (Ronda de Coronación):** ${res['mo_cap2']:,.2f} COP",
            f"- **Desglose por Cuadrilla y Jornales Totales:**",
            f"  - **Oficial de Obra (Código 6 @ ${self.P(6):,.0f}/día):** `{res['jornales_oficial']:.2f} jornales (días)` → **${res['costo_oficial']:,.2f} COP**",
            f"  - **Obrero / Ayudante (Código 5 @ ${self.P(5):,.0f}/día):** `{res['jornales_ayudante']:.2f} jornales (días)` → **${res['costo_ayudante']:,.2f} COP**",
            f"  - **Total Hombre-Días Requeridos:** `{res['jornales_totales']:.2f} jornales` (Equivalente a ~`{max(1, math.ceil(res['jornales_ayudante']/2.0))}` días hábiles con cuadrilla de 1 Oficial + 2 Ayudantes).",
            "",
            "### Mano de Obra por Actividad",
            "",
            "| Ítem | Actividad | Und | Cant. | M.O. Unitaria | Jornales Oficial | Jornales Ayudante | M.O. Total Actividad |",
            "| :---: | :--- | :---: | ---: | ---: | ---: | ---: | ---: |"
        ]

        for a in res["actividades"]:
            lineas.append(
                f"| {a['item']} | {a['nombre']} | {a['unidad']} | {a['cantidad']:.2f} | "
                f"${a['mo_unit']:,.2f} | {a['jornales_oficial_total']:.2f} d | {a['jornales_ayudante_total']:.2f} d | **${a['mo_total']:,.2f}** |"
            )

        lineas.extend([
            "",
            "---",
            "",
            "## 3. Presupuesto General por Actividades (12 Ítems)",
            "",
            "| Ítem | Cap. | Actividad | Und | Cantidad | Equipos Unit. | Materiales Unit. | Transp. Unit. | M.O. Unit. | Valor Unitario | Valor Total |",
            "| :---: | :---: | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        ])

        for a in res["actividades"]:
            lineas.append(
                f"| {a['item']} | {a['capitulo']} | {a['nombre']} | {a['unidad']} | {a['cantidad']:.2f} | "
                f"${a['eq_unit']:,.2f} | ${a['mat_unit']:,.2f} | ${a['trans_unit']:,.2f} | ${a['mo_unit']:,.2f} | "
                f"**${a['vr_unitario']:,.2f}** | **${a['vr_total']:,.2f}** |"
            )

        lineas.extend([
            "",
            "---",
            "",
            "## 4. Explosión Consolidada de Insumos (Lista de Compras y Contratación)",
            "",
            "| Cód. | Categoría | Insumo | Unidad | Precio Unitario | Cant. Exacta | Cant. Comercial Sugerida | Costo Total (COP) |",
            "| :---: | :--- | :--- | :---: | ---: | ---: | ---: | ---: |"
        ])

        for cod, exp in sorted(res["explosion_insumos"].items()):
            if exp["cantidad_total"] > 0:
                lineas.append(
                    f"| {cod} | {exp['categoria']} | {exp['nombre']} | {exp['unidad']} | "
                    f"${exp['precio_unitario']:,.2f} | {exp['cantidad_total']:.2f} | "
                    f"**{exp['cantidad_comercial_sugerida']} {exp['unidad']}** | **${exp['costo_total']:,.2f}** |"
                )

        contenido = "\n".join(lineas) + "\n"
        with open(ruta_md, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta_md


# =============================================================================
# 4. INTERFAZ GRÁFICA DE USUARIO (CUSTOMTKINTER)
# =============================================================================
def lanzar_gui(motor: MotorPresupuestoFiltro):
    import tkinter as tk
    from tkinter import ttk, messagebox
    import customtkinter as ctk

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class AppPresupuestoFiltroGUI(ctk.CTk):
        def __init__(self, motor_calc: MotorPresupuestoFiltro):
            super().__init__()
            self.motor = motor_calc
            self.title("💧 Sistema de Presupuesto APU, Mano de Obra e Insumos — Control de Inundación")
            self.geometry("1360x860")
            self.minsize(1150, 740)

            self.entries_insumos = {}
            self.entries_geom = {}
            self.entries_aiu = {}

            self._configurar_estilos_treeview()
            self._construir_encabezado_kpi()
            self._construir_pestanas()
            self._construir_barra_inferior()
            self.actualizar_toda_la_interfaz()

        def _configurar_estilos_treeview(self):
            style = ttk.Style()
            style.theme_use("clam")
            style.configure(
                "Custom.Treeview",
                background="#181825",
                foreground="#CDD6F4",
                fieldbackground="#181825",
                rowheight=28,
                font=("Sans", 10)
            )
            style.configure(
                "Custom.Treeview.Heading",
                background="#313244",
                foreground="#89B4FA",
                font=("Sans", 10, "bold")
            )
            style.map("Custom.Treeview", background=[("selected", "#45475A")])

        def _construir_encabezado_kpi(self):
            header = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=10)
            header.pack(fill="x", padx=14, pady=(10, 6))

            top_row = ctk.CTkFrame(header, fg_color="transparent")
            top_row.pack(fill="x", padx=14, pady=(8, 4))

            ctk.CTkLabel(
                top_row,
                text="💧 PROYECTO CONTROL DE INUNDACIÓN: FILTRO FRANCÉS + RONDA DE CORONACIÓN",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#89B4FA"
            ).pack(side="left")

            self.lbl_subtitulo = ctk.CTkLabel(
                top_row,
                text="",
                font=ctk.CTkFont(size=12),
                text_color="#A6ADC8"
            )
            self.lbl_subtitulo.pack(side="right")

            # Fila de Tarjetas KPI en Tiempo Real
            kpi_row = ctk.CTkFrame(header, fg_color="transparent")
            kpi_row.pack(fill="x", padx=10, pady=(4, 10))
            for i in range(5):
                kpi_row.grid_columnconfigure(i, weight=1)

            self.kpi_cap1 = self._crear_tarjeta_kpi(kpi_row, 0, "Cap. I: Filtro Francés", "#89DCEB")
            self.kpi_cap2 = self._crear_tarjeta_kpi(kpi_row, 1, "Cap. II: Ronda Coronación", "#94E2D5")
            self.kpi_mo = self._crear_tarjeta_kpi(kpi_row, 2, "👷 VALOR TOTAL MANO DE OBRA", "#F9E2AF")
            self.kpi_directo = self._crear_tarjeta_kpi(kpi_row, 3, "Costo Directo Total", "#A6E3A1")
            self.kpi_contrato = self._crear_tarjeta_kpi(kpi_row, 4, "💰 VALOR TOTAL CONTRATO (c/AIU)", "#CBA6F7")

        def _crear_tarjeta_kpi(self, parent, col_idx: int, titulo: str, color_valor: str):
            card = ctk.CTkFrame(parent, fg_color="#181825", corner_radius=8, border_width=1, border_color="#313244")
            card.grid(row=0, column=col_idx, padx=5, sticky="nsew")
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=11, weight="bold"), text_color="#BAC2DE").pack(pady=(6, 2))
            lbl_val = ctk.CTkLabel(card, text="$0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color=color_valor)
            lbl_val.pack(pady=(0, 2))
            lbl_det = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=10), text_color="#A6ADC8")
            lbl_det.pack(pady=(0, 6))
            return (lbl_val, lbl_det)

        def _construir_pestanas(self):
            self.tabview = ctk.CTkTabview(self, fg_color="#1E1E2E", corner_radius=10)
            self.tabview.pack(fill="both", expand=True, padx=14, pady=4)

            self.tab_presupuesto = self.tabview.add("📋 1. Presupuesto General y Geometría")
            self.tab_mano_obra = self.tabview.add("👷 2. Valor Total Mano de Obra y Cuadrillas")
            self.tab_insumos = self.tabview.add("🏷️ 3. Modificar Precios de Insumos (23)")
            self.tab_apu = self.tabview.add("🔍 4. Visor Detallado de APUs")
            self.tab_compras = self.tabview.add("🛒 5. Lista de Compras (Explosión)")
            self.tab_ficha = self.tabview.add("📐 6. Ficha Técnica (Presentación)")

            self._armar_tab_presupuesto()
            self._armar_tab_mano_obra()
            self._armar_tab_insumos()
            self._armar_tab_apu()
            self._armar_tab_compras()
            self._armar_tab_ficha()

        # ---------------------------------------------------------------------
        # PESTAÑA 1: PRESUPUESTO GENERAL Y PARÁMETROS GEOMÉTRICOS
        # ---------------------------------------------------------------------
        def _armar_tab_presupuesto(self):
            # Panel superior de parámetros rápidos (Longitudes y AIU)
            param_frame = ctk.CTkFrame(self.tab_presupuesto, fg_color="#181825", corner_radius=8)
            param_frame.pack(fill="x", padx=8, pady=(4, 8))

            ctk.CTkLabel(
                param_frame,
                text="⚙️ Parámetros Geométricos y AIU (Modifica y presiona 'Recalcular'):",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#F9E2AF"
            ).grid(row=0, column=0, columnspan=10, sticky="w", padx=12, pady=(8, 4))

            campos = [
                ("L_filtro_ml", "Long. Filtro Francés (ml):", 0, 1),
                ("ancho_zanja_filtro_m", "Ancho Zanja Filtro (m):", 0, 3),
                ("prof_zanja_filtro_m", "Prof. Zanja Filtro (m):", 0, 5),
                ("altura_grava_filtro_m", "Altura Grava (m):", 0, 7),
                ("L_ronda_ml", "Long. Ronda Coronación (ml):", 1, 1),
                ("espesor_concreto_ronda_m", "Espesor Concreto Ronda (m):", 1, 3),
            ]
            for key, label_txt, r, c in campos:
                ctk.CTkLabel(param_frame, text=label_txt, font=ctk.CTkFont(size=11)).grid(row=r+1, column=c-1, sticky="e", padx=(10, 4), pady=4)
                ent = ctk.CTkEntry(param_frame, width=80, height=28)
                ent.grid(row=r+1, column=c, sticky="w", padx=(0, 8), pady=4)
                self.entries_geom[key] = ent

            # AIU
            aiu_campos = [
                ("aiu_administracion_pct", "Admin (%):", 1, 5),
                ("aiu_imprevistos_pct", "Imprev (%):", 1, 7),
                ("aiu_utilidad_pct", "Utilidad (%):", 1, 9),
            ]
            for key, label_txt, r, c in aiu_campos:
                ctk.CTkLabel(param_frame, text=label_txt, font=ctk.CTkFont(size=11)).grid(row=r+1, column=c-1, sticky="e", padx=(8, 4), pady=4)
                ent = ctk.CTkEntry(param_frame, width=65, height=28)
                ent.grid(row=r+1, column=c, sticky="w", padx=(0, 8), pady=4)
                self.entries_aiu[key] = ent

            btn_apply_geom = ctk.CTkButton(
                param_frame,
                text="🔄 Aplicar Geometría y AIU",
                fg_color="#2E7D32",
                hover_color="#1B5E20",
                width=180,
                height=30,
                command=self.aplicar_cambios_geometria_y_aiu
            )
            btn_apply_geom.grid(row=1, column=8, columnspan=2, padx=10, pady=4)

            # Tabla Treeview de las 12 actividades
            tree_frame = ctk.CTkFrame(self.tab_presupuesto, fg_color="#181825", corner_radius=8)
            tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

            cols = ("item", "cap", "nombre", "und", "cant", "eq_u", "mat_u", "trans_u", "mo_u", "vr_unit", "mo_tot", "vr_total")
            self.tree_presupuesto = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Custom.Treeview")

            encabezados = [
                ("item", "Ítem", 45, "center"),
                ("cap", "Cap.", 45, "center"),
                ("nombre", "Descripción de la Actividad", 340, "w"),
                ("und", "Und", 45, "center"),
                ("cant", "Cantidad", 75, "e"),
                ("eq_u", "Equipos Unit.", 95, "e"),
                ("mat_u", "Materiales Unit.", 105, "e"),
                ("trans_u", "Transp. Unit.", 90, "e"),
                ("mo_u", "M.O. Unitaria", 95, "e"),
                ("vr_unit", "VALOR UNITARIO", 115, "e"),
                ("mo_tot", "M.O. Total Ítem", 110, "e"),
                ("vr_total", "VALOR TOTAL", 125, "e"),
            ]
            for col_id, text, width, anchor in encabezados:
                self.tree_presupuesto.heading(col_id, text=text)
                self.tree_presupuesto.column(col_id, width=width, anchor=anchor)

            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_presupuesto.yview)
            self.tree_presupuesto.configure(yscrollcommand=vsb.set)
            self.tree_presupuesto.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            vsb.pack(side="right", fill="y", pady=4)

        # ---------------------------------------------------------------------
        # PESTAÑA 2: VALOR TOTAL DE LA MANO DE OBRA Y CUADRILLAS
        # ---------------------------------------------------------------------
        def _armar_tab_mano_obra(self):
            top_mo = ctk.CTkFrame(self.tab_mano_obra, fg_color="#181825", corner_radius=8)
            top_mo.pack(fill="x", padx=8, pady=6)

            self.lbl_resumen_mo = ctk.CTkLabel(
                top_mo,
                text="",
                justify="left",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#F9E2AF"
            )
            self.lbl_resumen_mo.pack(anchor="w", padx=14, pady=10)

            tree_frame = ctk.CTkFrame(self.tab_mano_obra, fg_color="#181825", corner_radius=8)
            tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

            cols = ("item", "cap", "nombre", "und", "cant", "mo_unit", "j_oficial", "c_oficial", "j_ayudante", "c_ayudante", "mo_total", "pct_mo")
            self.tree_mo = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Custom.Treeview")

            headers = [
                ("item", "Ítem", 45, "center"),
                ("cap", "Cap.", 45, "center"),
                ("nombre", "Actividad del Presupuesto", 330, "w"),
                ("und", "Und", 45, "center"),
                ("cant", "Cant.", 70, "e"),
                ("mo_unit", "M.O. Unitaria", 100, "e"),
                ("j_oficial", "Jornales Oficial (d)", 115, "e"),
                ("c_oficial", "Costo Oficial ($)", 115, "e"),
                ("j_ayudante", "Jornales Ayudante (d)", 125, "e"),
                ("c_ayudante", "Costo Ayudante ($)", 115, "e"),
                ("mo_total", "VALOR TOTAL M.O.", 130, "e"),
                ("pct_mo", "% del Total M.O.", 95, "e")
            ]
            for cid, txt, w, anc in headers:
                self.tree_mo.heading(cid, text=txt)
                self.tree_mo.column(cid, width=w, anchor=anc)

            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_mo.yview)
            self.tree_mo.configure(yscrollcommand=vsb.set)
            self.tree_mo.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            vsb.pack(side="right", fill="y", pady=4)

        # ---------------------------------------------------------------------
        # PESTAÑA 3: EDITOR DE PRECIOS DE LOS 23 INSUMOS
        # ---------------------------------------------------------------------
        def _armar_tab_insumos(self):
            ctrl_bar = ctk.CTkFrame(self.tab_insumos, fg_color="#181825", corner_radius=8)
            ctrl_bar.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(
                ctrl_bar,
                text="✏️ Modifica el precio unitario de cualquier insumo (Materiales, Mano de Obra, Equipos, Transporte) y presiona 'Aplicar Nuevos Precios':",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#A6E3A1"
            ).pack(side="left", padx=12, pady=8)

            ctk.CTkButton(
                ctrl_bar,
                text="⚡ Aplicar Nuevos Precios y Recalcular Presupuesto",
                fg_color="#2E7D32",
                hover_color="#1B5E20",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self.aplicar_precios_insumos
            ).pack(side="right", padx=10, pady=6)

            ctk.CTkButton(
                ctrl_bar,
                text="↩️ Restaurar Precios Originales",
                fg_color="#45475A",
                hover_color="#585B70",
                command=self.restaurar_todo_original
            ).pack(side="right", padx=6, pady=6)

            scroll = ctk.CTkScrollableFrame(self.tab_insumos, fg_color="#181825", corner_radius=8)
            scroll.pack(fill="both", expand=True, padx=8, pady=4)

            headers = ["Cód.", "Categoría", "Nombre del Insumo", "Unidad", "Precio Base ($)", "Nuevo Precio Unitario ($)", "Cant. en Obra", "Costo Total en Obra ($)"]
            for c_idx, h_txt in enumerate(headers):
                ctk.CTkLabel(scroll, text=h_txt, font=ctk.CTkFont(size=11, weight="bold"), text_color="#89B4FA").grid(
                    row=0, column=c_idx, padx=8, pady=6, sticky="w" if c_idx in [1, 2] else "e"
                )

            self.lbls_insumo_cant = {}
            self.lbls_insumo_costo = {}

            for r_idx, (cod_str, ins) in enumerate(sorted(self.motor.datos["insumos"].items(), key=lambda x: int(x[0])), start=1):
                cod = ins["codigo"]
                cat_color = "#F9E2AF" if ins["categoria"] == "Mano de obra" else ("#89DCEB" if ins["categoria"] == "Equipos" else ("#CBA6F7" if ins["categoria"] == "Transporte" else "#CDD6F4"))

                ctk.CTkLabel(scroll, text=str(cod), font=ctk.CTkFont(size=11)).grid(row=r_idx, column=0, padx=8, pady=3, sticky="e")
                ctk.CTkLabel(scroll, text=ins["categoria"], font=ctk.CTkFont(size=11, weight="bold"), text_color=cat_color).grid(row=r_idx, column=1, padx=8, pady=3, sticky="w")
                ctk.CTkLabel(scroll, text=ins["nombre"], font=ctk.CTkFont(size=11)).grid(row=r_idx, column=2, padx=8, pady=3, sticky="w")
                ctk.CTkLabel(scroll, text=ins["unidad"], font=ctk.CTkFont(size=11)).grid(row=r_idx, column=3, padx=8, pady=3, sticky="e")
                ctk.CTkLabel(scroll, text=f"${ins['precio_base']:,.0f}", font=ctk.CTkFont(size=11), text_color="#A6ADC8").grid(row=r_idx, column=4, padx=8, pady=3, sticky="e")

                ent = ctk.CTkEntry(scroll, width=120, height=26, justify="right")
                ent.grid(row=r_idx, column=5, padx=8, pady=3)
                ent.bind("<Return>", lambda _e: self.aplicar_precios_insumos())
                self.entries_insumos[cod_str] = ent

                lbl_cant = ctk.CTkLabel(scroll, text="0.00", font=ctk.CTkFont(size=11))
                lbl_cant.grid(row=r_idx, column=6, padx=8, pady=3, sticky="e")
                self.lbls_insumo_cant[cod] = lbl_cant

                lbl_costo = ctk.CTkLabel(scroll, text="$0.00", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A6E3A1")
                lbl_costo.grid(row=r_idx, column=7, padx=8, pady=3, sticky="e")
                self.lbls_insumo_costo[cod] = lbl_costo

        # ---------------------------------------------------------------------
        # PESTAÑA 4: VISOR DETALLADO DE APUs POR ACTIVIDAD
        # ---------------------------------------------------------------------
        def _armar_tab_apu(self):
            sel_bar = ctk.CTkFrame(self.tab_apu, fg_color="#181825", corner_radius=8)
            sel_bar.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(sel_bar, text="Selecciona la Actividad para inspeccionar su APU:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=12, pady=8)

            acts = self.motor.definir_actividades_apu()
            opciones = [f"Ítem {a['item']} ({a['unidad']}) — {a['nombre']}" for a in acts]
            self.combo_apu = ctk.CTkComboBox(sel_bar, values=opciones, width=560, command=lambda _: self._actualizar_detalle_apu())
            self.combo_apu.pack(side="left", padx=10, pady=8)
            self.combo_apu.set(opciones[0])

            self.txt_apu = ctk.CTkTextbox(self.tab_apu, font=ctk.CTkFont(family="Monospace", size=12), fg_color="#181825")
            self.txt_apu.pack(fill="both", expand=True, padx=8, pady=4)

        # ---------------------------------------------------------------------
        # PESTAÑA 5: LISTA DE COMPRAS / EXPLOSIÓN DE INSUMOS
        # ---------------------------------------------------------------------
        def _armar_tab_compras(self):
            tree_frame = ctk.CTkFrame(self.tab_compras, fg_color="#181825", corner_radius=8)
            tree_frame.pack(fill="both", expand=True, padx=8, pady=6)

            cols = ("cod", "cat", "nombre", "und", "precio", "cant_exacta", "cant_comercial", "costo_total", "items_uso")
            self.tree_compras = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Custom.Treeview")

            headers = [
                ("cod", "Cód.", 50, "center"),
                ("cat", "Categoría", 110, "w"),
                ("nombre", "Insumo / Recurso Requerido", 340, "w"),
                ("und", "Unidad", 65, "center"),
                ("precio", "Precio Unit. ($)", 110, "e"),
                ("cant_exacta", "Cant. Exacta", 95, "e"),
                ("cant_comercial", "Cant. Comercial a Comprar", 160, "center"),
                ("costo_total", "Costo Total en Obra ($)", 140, "e"),
                ("items_uso", "Actividades donde interviene", 200, "w")
            ]
            for cid, txt, w, anc in headers:
                self.tree_compras.heading(cid, text=txt)
                self.tree_compras.column(cid, width=w, anchor=anc)

            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_compras.yview)
            self.tree_compras.configure(yscrollcommand=vsb.set)
            self.tree_compras.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            vsb.pack(side="right", fill="y", pady=4)

        # ---------------------------------------------------------------------
        # PESTAÑA 6: FICHA TÉCNICA DE LA PRESENTACIÓN (.ODP)
        # ---------------------------------------------------------------------
        def _armar_tab_ficha(self):
            txt = ctk.CTkTextbox(self.tab_ficha, font=ctk.CTkFont(family="Monospace", size=12), fg_color="#181825")
            txt.pack(fill="both", expand=True, padx=8, pady=6)
            ficha_info = (
                "====================================================================================================\n"
                "  FICHA TÉCNICA Y DIAGNÓSTICO DE INGENIERÍA (EXTRAÍDO DE 'Presentación Filtro.odp')\n"
                "====================================================================================================\n\n"
                "1. DIAGNÓSTICO DEL PROBLEMA EN EL PREDIO RURAL (ORIENTE ANTIOQUEÑO):\n"
                "   • Escorrentía superficial procedente de la ladera superior que impacta directamente la vivienda.\n"
                "   • Infiltración subsuperficial y ascenso de humedad capilar hacia la cimentación y muros.\n"
                "   • Solución Integral de Ingeniería en dos líneas de defensa:\n"
                "     - Línea 1 (Superior): Ronda / Cuneta de Coronación revestida en concreto para interceptar aguas lluvias.\n"
                "     - Línea 2 (Perimetral): Filtro Francés (Subdrenaje) para abatir el nivel freático y evacuar infiltraciones.\n\n"
                "2. ESPECIFICACIONES TÉCNICAS — CAPÍTULO I: FILTRO FRANCÉS (SUBDRENAJE):\n"
                "   • Geometría de Zanja: Ancho W = 0.40 m | Profundidad H = 0.80 m | Longitud base = 30.0 ml.\n"
                "   • Pendiente longitudinal garantizada: 1.0% a 2.0% hacia el punto de descole.\n"
                "   • Medio Filtrante: Grava triturada limpia de 3/4\" a 1-1/2\" (altura h_g = 0.60 m).\n"
                "   • Geosintético: Geotextil no tejido NT 1600 / NT 1800 recubriendo las paredes con traslapo superior >= 0.20 m.\n"
                "   • Tubería colectora: Tubería corrugada perforada de drenaje Ø 4\" (HDPE/PVC) con accesorios.\n"
                "   • Sello / Cobertura: Capa superior de cierre h_c = 0.20 m y conformación final.\n\n"
                "3. ESPECIFICACIONES TÉCNICAS — CAPÍTULO II: RONDA DE CORONACIÓN EN CONCRETO:\n"
                "   • Geometría Trapezoidal: Base menor b = 0.30 m | Taludes laterales = 0.41 m | Altura h = 0.30 - 0.40 m.\n"
                "   • Longitud base proyectada: 40.0 ml en cabecera de ladera + caballón de tierra aguas abajo.\n"
                "   • Estructura de Revestimiento: Concreto hidráulico de 2500 PSI (17.2 MPa) de espesor e = 7.5 cm (0.075 m).\n"
                "   • Impermeabilización y Refuerzo: Aditivo impermeabilizante integral Sika 1 + Malla electrosoldada M-084 / Q-106.\n"
                "   • Control de Fisuración: Juntas de dilatación selladas con poliuretano/elastómero cada 2.50 m a 3.00 m y curado.\n"
            )
            txt.insert("1.0", ficha_info)
            txt.configure(state="disabled")

        # ---------------------------------------------------------------------
        # BARRA INFERIOR DE ACCIONES Y SINCRONIZACIÓN ODS
        # ---------------------------------------------------------------------
        def _construir_barra_inferior(self):
            footer = ctk.CTkFrame(self, fg_color="#181825", corner_radius=8)
            footer.pack(fill="x", padx=14, pady=(2, 10))

            self.lbl_estado = ctk.CTkLabel(
                footer,
                text="✅ Sistema listo. Todos los cálculos coinciden al 100% con 'Presupuesto Filtro.ods'.",
                font=ctk.CTkFont(size=12),
                text_color="#A6E3A1"
            )
            self.lbl_estado.pack(side="left", padx=12, pady=8)

            ctk.CTkButton(
                footer,
                text="💾 Guardar y Sincronizar con 'Presupuesto Filtro.ods'",
                fg_color="#1565C0",
                hover_color="#0D47A1",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self.accion_sincronizar_ods
            ).pack(side="right", padx=10, pady=6)

            ctk.CTkButton(
                footer,
                text="📄 Exportar Reporte Markdown",
                fg_color="#313244",
                hover_color="#45475A",
                command=self.accion_exportar_markdown
            ).pack(side="right", padx=6, pady=6)

        # ---------------------------------------------------------------------
        # EVENTOS Y ACTUALIZACIÓN DE INTERFAZ
        # ---------------------------------------------------------------------
        def actualizar_toda_la_interfaz(self):
            res = self.motor.calcular_resumen_general()
            g = self.motor.datos["geometria"]
            p = self.motor.datos["proyecto"]

            self.lbl_subtitulo.configure(text=f"{p['ubicacion']} | Filtro: {g['L_filtro_ml']:.1f} ml | Ronda: {g['L_ronda_ml']:.1f} ml")

            # Actualizar KPIs
            self.kpi_cap1[0].configure(text=f"${res['subtotal_cap1']:,.2f}")
            self.kpi_cap1[1].configure(text=f"Long: {g['L_filtro_ml']:.1f} ml | M.O.: ${res['mo_cap1']:,.0f}")

            self.kpi_cap2[0].configure(text=f"${res['subtotal_cap2']:,.2f}")
            self.kpi_cap2[1].configure(text=f"Long: {g['L_ronda_ml']:.1f} ml | M.O.: ${res['mo_cap2']:,.0f}")

            pct_mo_cd = (res["total_mano_de_obra"] / res["costo_directo"] * 100.0) if res["costo_directo"] > 0 else 0.0
            self.kpi_mo[0].configure(text=f"${res['total_mano_de_obra']:,.2f}")
            self.kpi_mo[1].configure(text=f"{pct_mo_cd:.1f}% del C.D. | {res['jornales_totales']:.1f} jornales totales")

            self.kpi_directo[0].configure(text=f"${res['costo_directo']:,.2f}")
            self.kpi_directo[1].configure(text=f"Mat: ${res['total_materiales']:,.0f} | Eq+Tr: ${(res['total_equipos']+res['total_transporte']):,.0f}")

            self.kpi_contrato[0].configure(text=f"${res['vr_total_contrato']:,.2f}")
            self.kpi_contrato[1].configure(text=f"Incluye AIU ({res['pct_aiu_total']:.1f}%): ${res['vr_aiu']:,.2f}")

            # Poblar campos de geometría y AIU
            for key, ent in self.entries_geom.items():
                ent.delete(0, "end")
                ent.insert(0, str(g[key]))
            for key, ent in self.entries_aiu.items():
                ent.delete(0, "end")
                ent.insert(0, str(p[key]))

            # Poblar Tabla 1: Presupuesto General
            for item in self.tree_presupuesto.get_children():
                self.tree_presupuesto.delete(item)
            for a in res["actividades"]:
                self.tree_presupuesto.insert("", "end", values=(
                    a["item"],
                    a["capitulo"],
                    a["nombre"],
                    a["unidad"],
                    f"{a['cantidad']:.2f}",
                    f"${a['eq_unit']:,.2f}",
                    f"${a['mat_unit']:,.2f}",
                    f"${a['trans_unit']:,.2f}",
                    f"${a['mo_unit']:,.2f}",
                    f"${a['vr_unitario']:,.2f}",
                    f"${a['mo_total']:,.2f}",
                    f"${a['vr_total']:,.2f}"
                ))
            # Filas de resumen en Tabla 1
            self.tree_presupuesto.insert("", "end", values=("", "I", "SUBTOTAL CAPÍTULO I: FILTRO FRANCÉS", "", "", "", "", "", "", "", f"${res['mo_cap1']:,.2f}", f"${res['subtotal_cap1']:,.2f}"))
            self.tree_presupuesto.insert("", "end", values=("", "II", "SUBTOTAL CAPÍTULO II: RONDA DE CORONACIÓN", "", "", "", "", "", "", "", f"${res['mo_cap2']:,.2f}", f"${res['subtotal_cap2']:,.2f}"))
            self.tree_presupuesto.insert("", "end", values=("", "", "COSTO DIRECTO TOTAL DE OBRA", "", "", "", "", "", "", "", f"${res['total_mano_de_obra']:,.2f}", f"${res['costo_directo']:,.2f}"))
            self.tree_presupuesto.insert("", "end", values=("", "", f"TOTAL A.I.U. ({res['pct_aiu_total']:.1f}%)", "", "", "", "", "", "", "", "", f"${res['vr_aiu']:,.2f}"))
            self.tree_presupuesto.insert("", "end", values=("", "", "VALOR TOTAL DEL CONTRATO", "", "", "", "", "", "", "", "", f"${res['vr_total_contrato']:,.2f}"))

            # Poblar Tabla 2: Mano de Obra
            dias_cuadrilla = max(1, math.ceil(res["jornales_ayudante"] / 2.0))
            resumen_mo_txt = (
                f"👷 VALOR TOTAL DE LA MANO DE OBRA DIRECTA: ${res['total_mano_de_obra']:,.2f} COP  ({pct_mo_cd:.1f}% del Costo Directo Total)\n"
                f"   • Oficial de Obra (Cód. 6 @ ${self.motor.P(6):,.0f}/día):  {res['jornales_oficial']:.2f} jornales (días)  =  ${res['costo_oficial']:,.2f} COP\n"
                f"   • Obrero / Ayudante (Cód. 5 @ ${self.motor.P(5):,.0f}/día): {res['jornales_ayudante']:.2f} jornales (días)  =  ${res['costo_ayudante']:,.2f} COP\n"
                f"   • Total Jornales Hombre-Día: {res['jornales_totales']:.2f} días  |  Duración estimada con 1 Oficial + 2 Ayudantes: ~{dias_cuadrilla} días hábiles de ejecución."
            )
            self.lbl_resumen_mo.configure(text=resumen_mo_txt)

            for item in self.tree_mo.get_children():
                self.tree_mo.delete(item)
            for a in res["actividades"]:
                pct_item = (a["mo_total"] / res["total_mano_de_obra"] * 100.0) if res["total_mano_de_obra"] > 0 else 0.0
                self.tree_mo.insert("", "end", values=(
                    a["item"],
                    a["capitulo"],
                    a["nombre"],
                    a["unidad"],
                    f"{a['cantidad']:.2f}",
                    f"${a['mo_unit']:,.2f}",
                    f"{a['jornales_oficial_total']:.2f} d",
                    f"${a['costo_oficial_total']:,.2f}",
                    f"{a['jornales_ayudante_total']:.2f} d",
                    f"${a['costo_ayudante_total']:,.2f}",
                    f"${a['mo_total']:,.2f}",
                    f"{pct_item:.1f}%"
                ))
            self.tree_mo.insert("", "end", values=(
                "", "", "TOTAL CONSOLIDADO MANO DE OBRA EN EL PROYECTO", "", "", "",
                f"{res['jornales_oficial']:.2f} d", f"${res['costo_oficial']:,.2f}",
                f"{res['jornales_ayudante']:.2f} d", f"${res['costo_ayudante']:,.2f}",
                f"${res['total_mano_de_obra']:,.2f}", "100.0%"
            ))

            # Poblar Pestaña 3: Editor de Insumos
            for cod_str, ent in self.entries_insumos.items():
                cod = int(cod_str)
                precio_actual = self.motor.datos["insumos"][cod_str]["precio"]
                ent.delete(0, "end")
                ent.insert(0, f"{precio_actual:.0f}" if precio_actual % 1 == 0 else f"{precio_actual:.2f}")
                exp = res["explosion_insumos"][cod]
                self.lbls_insumo_cant[cod].configure(text=f"{exp['cantidad_total']:.2f} {exp['unidad']}")
                self.lbls_insumo_costo[cod].configure(text=f"${exp['costo_total']:,.2f}")

            # Poblar Pestaña 4: Detalle APU
            self._actualizar_detalle_apu()

            # Poblar Pestaña 5: Explosión de Insumos
            for item in self.tree_compras.get_children():
                self.tree_compras.delete(item)
            for cod, exp in sorted(res["explosion_insumos"].items()):
                usos = ", ".join(exp["actividades_uso"]) if exp["actividades_uso"] else "Reserva / No usado en APU actual"
                self.tree_compras.insert("", "end", values=(
                    cod,
                    exp["categoria"],
                    exp["nombre"],
                    exp["unidad"],
                    f"${exp['precio_unitario']:,.2f}",
                    f"{exp['cantidad_total']:.2f}",
                    f"{exp['cantidad_comercial_sugerida']} {exp['unidad']}",
                    f"${exp['costo_total']:,.2f}",
                    usos
                ))

        def _actualizar_detalle_apu(self):
            sel = self.combo_apu.get()
            try:
                item_num = int(sel.split()[1])
            except Exception:
                item_num = 1
            res = self.motor.calcular_resumen_general()
            act = next((a for a in res["actividades"] if a["item"] == item_num), res["actividades"][0])

            lineas = [
                f"====================================================================================================",
                f"  ANÁLISIS DE PRECIO UNITARIO (APU) — ÍTEM {act['item']}: {act['nombre']}",
                f"====================================================================================================",
                f"  Capítulo:          {act['capitulo_nombre']}",
                f"  Unidad de Medida:  {act['unidad']}   |   Cantidad en Obra: {act['cantidad']:.2f} {act['unidad']} ({act['formula_cantidad']})",
                f"  Valor Unitario:    ${act['vr_unitario']:,.2f} / {act['unidad']}   |   Valor Total Actividad: ${act['vr_total']:,.2f} COP",
                f"----------------------------------------------------------------------------------------------------",
                f"  {'Cód.':<6} {'Descripción del Recurso':<50} {'Und':<8} {'Rendim.':>10} {'Vr. Unitario':>14} {'Subtotal Unit.':>15}",
                f"----------------------------------------------------------------------------------------------------"
            ]

            secciones = [
                ("I. EQUIPOS Y HERRAMIENTA", act["detalle_eq"], act["eq_unit"]),
                ("II. MATERIALES EN OBRA", act["detalle_mat"], act["mat_unit"]),
                ("III. TRANSPORTE Y ACARREOS", act["detalle_trans"], act["trans_unit"]),
                ("IV. MANO DE OBRA", act["detalle_mo"], act["mo_unit"]),
            ]
            for titulo_sec, lista_det, sub_sec in secciones:
                lineas.append(f"\n  [{titulo_sec}]")
                if not lista_det:
                    lineas.append("     (Sin insumos en esta categoría)")
                for d in lista_det:
                    cod_txt = str(d["codigo"]) if d["codigo"] > 0 else "%"
                    lineas.append(
                        f"  {cod_txt:<6} {d['nombre'][:49]:<50} {d['unidad']:<8} "
                        f"{d['rendimiento']:>10.4f} ${d['precio_unitario']:>13,.2f} ${d['subtotal_unitario']:>14,.2f}"
                    )
                lineas.append(f"  {'':<6} {'SUBTOTAL ' + titulo_sec:<50} {'':<8} {'':>10} {'':>14} ${sub_sec:>14,.2f}")

            lineas.extend([
                f"\n====================================================================================================",
                f"  TOTAL PRECIO UNITARIO ÍTEM {act['item']} ({act['unidad']}):   ${act['vr_unitario']:,.2f} COP",
                f"  TOTAL ACTIVIDAD PARA {act['cantidad']:.2f} {act['unidad']}:          ${act['vr_total']:,.2f} COP",
                f"  (De los cuales Mano de Obra Total en esta actividad = ${act['mo_total']:,.2f} COP)",
                f"===================================================================================================="
            ])

            self.txt_apu.configure(state="normal")
            self.txt_apu.delete("1.0", "end")
            self.txt_apu.insert("1.0", "\n".join(lineas))
            self.txt_apu.configure(state="disabled")

        def aplicar_cambios_geometria_y_aiu(self):
            try:
                for key, ent in self.entries_geom.items():
                    val = float(ent.get().replace(",", ".").strip())
                    if val <= 0:
                        raise ValueError(f"El parámetro {key} debe ser mayor que cero.")
                    self.motor.datos["geometria"][key] = val
                for key, ent in self.entries_aiu.items():
                    val = float(ent.get().replace(",", ".").strip())
                    if val < 0:
                        raise ValueError(f"El porcentaje {key} no puede ser negativo.")
                    self.motor.datos["proyecto"][key] = val

                self.motor.guardar_datos()
                self.actualizar_toda_la_interfaz()
                self.lbl_estado.configure(text="✅ Geometría y porcentajes AIU actualizados. Presupuesto recalculado.", text_color="#A6E3A1")
            except Exception as e:
                messagebox.showerror("Error en parámetros", f"Verifica los valores numéricos ingresados:\n{e}")

        def aplicar_precios_insumos(self):
            try:
                cambios = 0
                for cod_str, ent in self.entries_insumos.items():
                    limpio = ent.get().replace("$", "").replace(",", "").strip()
                    nuevo_val = float(limpio)
                    if nuevo_val < 0:
                        raise ValueError(f"El insumo {cod_str} no puede tener precio negativo.")
                    if abs(nuevo_val - self.motor.datos["insumos"][cod_str]["precio"]) > 1e-4:
                        cambios += 1
                    self.motor.datos["insumos"][cod_str]["precio"] = nuevo_val

                self.motor.guardar_datos()
                self.actualizar_toda_la_interfaz()
                self.lbl_estado.configure(
                    text=f"✅ Se actualizaron los precios de los insumos ({cambios} modificados) y se recalcularon las 12 actividades.",
                    text_color="#A6E3A1"
                )
            except Exception as e:
                messagebox.showerror("Error en precio de insumo", f"Verifica que todos los precios sean números válidos:\n{e}")

        def restaurar_todo_original(self):
            if messagebox.askyesno("Restaurar valores originales", "¿Deseas restaurar todos los precios de insumos y dimensiones a los valores originales del archivo Presupuesto Filtro.ods?"):
                self.motor.restaurar_valores_originales()
                self.actualizar_toda_la_interfaz()
                self.lbl_estado.configure(text="↩️ Valores originales restaurados al 100%.", text_color="#F9E2AF")

        def accion_sincronizar_ods(self):
            self.aplicar_precios_insumos()
            self.aplicar_cambios_geometria_y_aiu()
            ok, msg = self.motor.sincronizar_archivo_ods()
            self.motor.generar_reporte_markdown()
            if ok:
                self.lbl_estado.configure(text=f"💾 {msg}", text_color="#89DCEB")
                messagebox.showinfo("Sincronización Exitosa", f"{msg}\n\nTambién se actualizó 'Reporte_Presupuesto_y_Mano_de_Obra.md'.")
            else:
                messagebox.showerror("Error al sincronizar ODS", msg)

        def accion_exportar_markdown(self):
            ruta = self.motor.generar_reporte_markdown()
            self.lbl_estado.configure(text=f"📄 Reporte exportado en: {os.path.basename(ruta)}", text_color="#89B4FA")
            messagebox.showinfo("Reporte Generado", f"Reporte técnico y de mano de obra guardado en:\n{ruta}")

    app = AppPresupuestoFiltroGUI(motor)
    app.mainloop()


# =============================================================================
# 5. MODO CONSOLA INTERACTIVO Y RESUMEN RÁPIDO (--cli / --resumen)
# =============================================================================
def imprimir_resumen_consola(motor: MotorPresupuestoFiltro):
    res = motor.calcular_resumen_general()
    g = motor.datos["geometria"]

    print("\n" + "=" * 105)
    print(f"  💧 PRESUPUESTO Y CONTROL DE COSTOS: {motor.datos['proyecto']['nombre']}")
    print(f"  Filtro Francés: {g['L_filtro_ml']:.1f} ml  |  Ronda de Coronación: {g['L_ronda_ml']:.1f} ml")
    print("=" * 105)
    print(f"{'Ítem':<5} {'Cap':<4} {'Actividad':<52} {'Und':<4} {'Cant.':>7} {'M.O. Unit':>12} {'Vr. Unitario':>14} {'Valor Total':>15}")
    print("-" * 105)
    for a in res["actividades"]:
        print(
            f"{a['item']:<5} {a['capitulo']:<4} {a['nombre'][:51]:<52} {a['unidad']:<4} "
            f"{a['cantidad']:>7.2f} ${a['mo_unit']:>11,.2f} ${a['vr_unitario']:>13,.2f} ${a['vr_total']:>14,.2f}"
        )
    print("-" * 105)
    print(f"{'SUBTOTAL CAPÍTULO I (FILTRO FRANCÉS):':<75} ${res['subtotal_cap1']:>28,.2f}")
    print(f"{'SUBTOTAL CAPÍTULO II (RONDA DE CORONACIÓN):':<75} ${res['subtotal_cap2']:>28,.2f}")
    print(f"{'COSTO DIRECTO TOTAL DE OBRA:':<75} ${res['costo_directo']:>28,.2f}")
    aiu_lbl = f"TOTAL A.I.U. ({res['pct_aiu_total']:.1f}%):"
    print(f"{aiu_lbl:<75} ${res['vr_aiu']:>28,.2f}")
    print(f"{'VALOR TOTAL DEL CONTRATO (CON AIU):':<75} ${res['vr_total_contrato']:>28,.2f}")
    print("=" * 105)

    pct_mo = (res["total_mano_de_obra"] / res["costo_directo"] * 100.0) if res["costo_directo"] > 0 else 0.0
    print("\n" + "=" * 105)
    print("  👷 DESGLOSE DEL VALOR TOTAL DE LA MANO DE OBRA")
    print("=" * 105)
    print(f"  • VALOR TOTAL MANO DE OBRA DIRECTA:   ${res['total_mano_de_obra']:,.2f} COP  ({pct_mo:.2f}% del Costo Directo)")
    print(f"    - Mano de Obra Capítulo I (Filtro): ${res['mo_cap1']:,.2f} COP")
    print(f"    - Mano de Obra Capítulo II (Ronda): ${res['mo_cap2']:,.2f} COP")
    print(f"  • Oficial de Obra (Cód. 6 @ ${motor.P(6):,.0f}/día):  {res['jornales_oficial']:.2f} jornales  ->  ${res['costo_oficial']:,.2f} COP")
    print(f"  • Obrero/Ayudante (Cód. 5 @ ${motor.P(5):,.0f}/día):  {res['jornales_ayudante']:.2f} jornales  ->  ${res['costo_ayudante']:,.2f} COP")
    print(f"  • Total Jornales del Proyecto:        {res['jornales_totales']:.2f} jornales hombre-día")
    print("=" * 105)


def menu_cli_interactivo(motor: MotorPresupuestoFiltro):
    while True:
        imprimir_resumen_consola(motor)
        print("\nOpciones del Sistema:")
        print("  [1] Ver tabla de los 23 Insumos y modificar el precio de un insumo")
        print("  [2] Modificar longitudes del proyecto (L_filtro / L_ronda)")
        print("  [3] Ver Explosión de Insumos (Lista de compras consolidada)")
        print("  [4] Sincronizar cambios con 'Presupuesto Filtro.ods' y generar Reporte Markdown")
        print("  [5] Restaurar precios y dimensiones originales")
        print("  [0] Salir")
        op = input("\nSeleccione una opción: ").strip()

        if op == "1":
            res = motor.calcular_resumen_general()
            print("\n" + "-" * 95)
            print(f"{'Cód':<5} {'Categoría':<14} {'Nombre del Insumo':<46} {'Und':<8} {'Precio Actual':>14}")
            print("-" * 95)
            for cod_str, ins in sorted(motor.datos["insumos"].items(), key=lambda x: int(x[0])):
                print(f"{ins['codigo']:<5} {ins['categoria']:<14} {ins['nombre'][:45]:<46} {ins['unidad']:<8} ${ins['precio']:>13,.2f}")
            print("-" * 95)
            cod_in = input("Ingrese el código del insumo a modificar (2-24) o Enter para cancelar: ").strip()
            if cod_in in motor.datos["insumos"]:
                try:
                    nuevo_p = float(input(f"Nuevo precio unitario para '{motor.datos['insumos'][cod_in]['nombre']}': ").replace(",", ""))
                    motor.datos["insumos"][cod_in]["precio"] = nuevo_p
                    motor.guardar_datos()
                    print("✅ Precio actualizado y presupuesto recalculado.")
                except ValueError:
                    print("❌ Valor numérico inválido.")
        elif op == "2":
            try:
                lf = input(f"Nueva longitud Filtro Francés en ml [actual={motor.datos['geometria']['L_filtro_ml']}]: ").strip()
                if lf:
                    motor.datos["geometria"]["L_filtro_ml"] = float(lf)
                lr = input(f"Nueva longitud Ronda de Coronación en ml [actual={motor.datos['geometria']['L_ronda_ml']}]: ").strip()
                if lr:
                    motor.datos["geometria"]["L_ronda_ml"] = float(lr)
                motor.guardar_datos()
                print("✅ Longitudes actualizadas.")
            except ValueError:
                print("❌ Valor inválido.")
        elif op == "3":
            res = motor.calcular_resumen_general()
            print("\n" + "-" * 95)
            print(f"{'Cód':<5} {'Insumo':<44} {'Und':<8} {'Cant. Exacta':>12} {'Compra Sug.':>12} {'Costo Total':>14}")
            print("-" * 95)
            for cod, exp in sorted(res["explosion_insumos"].items()):
                if exp["cantidad_total"] > 0:
                    print(
                        f"{cod:<5} {exp['nombre'][:43]:<44} {exp['unidad']:<8} "
                        f"{exp['cantidad_total']:>12.2f} {str(exp['cantidad_comercial_sugerida']):>12} ${exp['costo_total']:>13,.2f}"
                    )
            input("\nPresione Enter para continuar...")
        elif op == "4":
            ok, msg = motor.sincronizar_archivo_ods()
            ruta_md = motor.generar_reporte_markdown()
            print(f"\n{msg}\nReporte generado en: {ruta_md}")
            input("\nPresione Enter para continuar...")
        elif op == "5":
            motor.restaurar_valores_originales()
            print("↩️ Valores originales restaurados.")
        elif op == "0":
            break


def main():
    parser = argparse.ArgumentParser(description="Aplicación de Presupuesto APU y Mano de Obra — Control de Inundación")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en menú interactivo por consola")
    parser.add_argument("--resumen", action="store_true", help="Imprimir resumen completo, generar reporte MD y salir")
    parser.add_argument("--sync-ods", action="store_true", help="Sincronizar datos actuales con Presupuesto Filtro.ods")
    args = parser.parse_args()

    motor = MotorPresupuestoFiltro()

    if args.sync_ods:
        ok, msg = motor.sincronizar_archivo_ods()
        print(msg)

    if args.resumen:
        imprimir_resumen_consola(motor)
        ruta = motor.generar_reporte_markdown()
        print(f"\n📄 Reporte Markdown actualizado en: {ruta}")
        return

    if args.cli or not os.environ.get("DISPLAY"):
        menu_cli_interactivo(motor)
    else:
        try:
            lanzar_gui(motor)
        except Exception as e:
            print(f"Aviso GUI ({e}). Iniciando modo consola interactivo...")
            menu_cli_interactivo(motor)


if __name__ == "__main__":
    main()
