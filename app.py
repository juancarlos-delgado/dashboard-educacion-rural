"""
================================================================================
Dashboard Estratégico del Ecosistema de Educación Rural en Colombia
================================================================================
Tercera entrega - Curso Big Data | Universidad Piloto de Colombia - 2026
Profesor: Sergio David Díaz Veru

Integrantes:
- Daniel Leonardo Gómez Mora
- Karen Viviana Ávila Holguín
- Javier José Niño Ballesteros
- Juan Carlos Delgado Campuzano

VERSIÓN ROBUSTA: con manejo de errores, encoding correcto y diagnósticos detallados.
================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table, no_update
import dash_bootstrap_components as dbc

# ============================================================
# 1. CONFIGURACIÓN DE COLORES
# ============================================================
COLOR_URBANO = "#2196F3"
COLOR_RURAL = "#FF9800"
COLOR_PDET = "#E53935"
COLOR_BOGOTA = "#1A237E"
COLOR_PROMEDIO = "#43A047"
COLOR_NEUTRO = "#757575"
COLOR_ACCENT = "#00BCD4"
PALETTE_ZONA = {"Urbano": COLOR_URBANO, "Rural": COLOR_RURAL}
DATA_DIR = "data"

# ============================================================
# 2. CARGA DE DATOS CON MÚLTIPLES ENCODINGS
# ============================================================
def cargar_csv(filename, encodings=None, **kwargs):
    """Carga un CSV probando múltiples encodings."""
    if encodings is None:
        encodings = ["utf-8", "latin-1", "cp1252"]
    ruta = os.path.join(DATA_DIR, filename)
    if not os.path.exists(ruta):
        print(f"  ✗ ARCHIVO NO ENCONTRADO: {ruta}")
        return pd.DataFrame()
    for enc in encodings:
        try:
            df = pd.read_csv(ruta, low_memory=False, encoding=enc, **kwargs)
            print(f"  ✓ {filename}: {len(df):,} filas x {df.shape[1]} cols (enc={enc})")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  ✗ ERROR al cargar {filename} con {enc}: {e}")
    print(f"  ✗ {filename}: no se pudo decodificar con ningún encoding")
    return pd.DataFrame()

print("=" * 70)
print("CARGANDO DATASETS...")
print("=" * 70)

df_saber11 = cargar_csv("df_saber11_clean.csv")
df_matricula = cargar_csv("df_matricula_clean.csv")
df_etdh_inst = cargar_csv("df_etdh_inst_clean.csv")
df_etdh_prog = cargar_csv("df_etdh_prog_clean.csv")
df_sena_desercion = cargar_csv("df_sena_desercion_clean.csv")
# DIVIPOLA con encoding latin-1 obligatorio
df_divipola = cargar_csv("DIVIPOLA-_Códigos_municipios_20250823.csv",
                          encodings=["latin-1", "cp1252", "utf-8"])

# ============================================================
# 3. DIAGNÓSTICO DETALLADO DE COLUMNAS
# ============================================================
print("\n" + "=" * 70)
print("DIAGNÓSTICO DE COLUMNAS")
print("=" * 70)
for name, df in [("Saber11", df_saber11), ("Matricula", df_matricula),
                  ("ETDH_Inst", df_etdh_inst), ("ETDH_Prog", df_etdh_prog),
                  ("SENA_Desercion", df_sena_desercion), ("DIVIPOLA", df_divipola)]:
    if not df.empty:
        print(f"\n[{name}] {len(df):,} filas")
        print(f"  Columnas: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")

# ============================================================
# 4. ENRIQUECIMIENTO DE COLUMNAS DERIVADAS EN SABER 11
# ============================================================
print("\n" + "=" * 70)
print("ENRIQUECIENDO SABER 11...")
print("=" * 70)

if not df_saber11.empty:
    # Zona_Clean: aceptar variantes
    if "cole_area_ubicacion" in df_saber11.columns:
        df_saber11["Zona_Clean"] = (df_saber11["cole_area_ubicacion"]
                                    .astype(str).str.upper().str.strip()
                                    .map(lambda x: "Urbano" if x == "URBANO" else "Rural"))
        print(f"  ✓ Zona_Clean creada: {df_saber11['Zona_Clean'].value_counts().to_dict()}")

    # Tiene_Internet: aceptar variantes
    if "fami_tieneinternet" in df_saber11.columns:
        df_saber11["Tiene_Internet"] = (df_saber11["fami_tieneinternet"]
                                        .astype(str).str.upper().str.strip()
                                        .isin(["SI", "SÍ", "YES", "1"])).astype(int)
        print(f"  ✓ Tiene_Internet creada: media={df_saber11['Tiene_Internet'].mean():.3f}")

    # Tiene_Computador
    if "fami_tienecomputador" in df_saber11.columns:
        df_saber11["Tiene_Computador"] = (df_saber11["fami_tienecomputador"]
                                          .astype(str).str.upper().str.strip()
                                          .isin(["SI", "SÍ", "YES", "1"])).astype(int)
        print(f"  ✓ Tiene_Computador creada: media={df_saber11['Tiene_Computador'].mean():.3f}")

    # Estrato_Num: extraer número
    if "fami_estratovivienda" in df_saber11.columns:
        df_saber11["Estrato_Num"] = (df_saber11["fami_estratovivienda"]
                                     .astype(str).str.extract(r"(\d+)").astype(float))
        print(f"  ✓ Estrato_Num creada. Distribución: {df_saber11['Estrato_Num'].value_counts(dropna=False).head().to_dict()}")

    # Punt_global como float
    if "punt_global" in df_saber11.columns:
        df_saber11["punt_global"] = pd.to_numeric(df_saber11["punt_global"], errors="coerce")

# ============================================================
# 5. FUNCIONES AUXILIARES
# ============================================================
def filtrar_saber11(departamentos, zona, estratos):
    df = df_saber11.copy()
    if df.empty:
        return df
    if departamentos and "cole_depto_ubicacion" in df.columns:
        df = df[df["cole_depto_ubicacion"].isin(departamentos)]
    if zona and "Zona_Clean" in df.columns:
        df = df[df["Zona_Clean"].isin(zona)]
    if estratos and "Estrato_Num" in df.columns:
        df = df[df["Estrato_Num"].isin([float(e) for e in estratos])]
    return df

def kpi_card(titulo, valor, color, subtitulo=""):
    return dbc.Card(
        dbc.CardBody([
            html.H6(titulo, className="text-muted mb-1", style={"fontSize": "12px"}),
            html.H2(valor, className="mb-0", style={"color": color, "fontWeight": "bold"}),
            html.Small(subtitulo, className="text-muted") if subtitulo else html.Span(),
        ]),
        style={"borderLeft": f"5px solid {color}",
               "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"}
    )

def fig_vacia(mensaje="Sin datos disponibles"):
    fig = go.Figure()
    fig.add_annotation(text=mensaje, xref="paper", yref="paper",
                      x=0.5, y=0.5, showarrow=False, font={"size": 14})
    fig.update_layout(height=300, xaxis={"visible": False}, yaxis={"visible": False})
    return fig

# ============================================================
# 6. INICIALIZACIÓN APP
# ============================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
           title="Dashboard Educación Rural", suppress_callback_exceptions=True)
server = app.server

# Listas para filtros
deptos_disponibles = []
if not df_saber11.empty and "cole_depto_ubicacion" in df_saber11.columns:
    deptos_disponibles = sorted(df_saber11["cole_depto_ubicacion"].dropna().unique())
    print(f"\n  Departamentos disponibles: {len(deptos_disponibles)}")

# ============================================================
# 7. LAYOUT
# ============================================================
header = dbc.Container([
    html.Div([
        html.H2("Dashboard Estratégico: Educación Rural en Colombia",
                style={"color": "white", "marginBottom": "0"}),
        html.P("Universidad Piloto de Colombia · CSE10C2 Big Data · 2026",
              style={"color": "#E3F2FD", "marginBottom": "0"}),
    ], style={
        "background": f"linear-gradient(135deg, {COLOR_BOGOTA} 0%, {COLOR_URBANO} 100%)",
        "padding": "20px 30px", "borderRadius": "0 0 10px 10px", "marginBottom": "20px"
    })
], fluid=True)

filtros = dbc.Card(dbc.CardBody([
    dbc.Row([
        dbc.Col([
            html.Label("Departamento", className="fw-bold"),
            dcc.Dropdown(id="filtro-depto",
                options=[{"label": d, "value": d} for d in deptos_disponibles],
                multi=True, placeholder="Todos los departamentos"),
        ], md=5),
        dbc.Col([
            html.Label("Zona", className="fw-bold"),
            dcc.Dropdown(id="filtro-zona",
                options=[{"label": "Urbano", "value": "Urbano"},
                         {"label": "Rural", "value": "Rural"}],
                multi=True, placeholder="Ambas zonas"),
        ], md=3),
        dbc.Col([
            html.Label("Estrato", className="fw-bold"),
            dcc.Dropdown(id="filtro-estrato",
                options=[{"label": f"Estrato {i}", "value": i} for i in range(1, 7)],
                multi=True, placeholder="Todos los estratos"),
        ], md=4),
    ])
]), className="mb-3")

footer = html.Footer([
    html.Hr(),
    html.P([
        html.Strong("Integrantes: "),
        "Daniel Leonardo Gómez Mora · Karen Viviana Ávila Holguín · ",
        "Javier José Niño Ballesteros · Juan Carlos Delgado Campuzano",
        html.Br(),
        html.Em("Curso CSE10C2 Big Data · Profesor Sergio David Díaz Veru · Junio 2026")
    ], className="text-center text-muted", style={"fontSize": "12px"})
], className="mt-4")

tab1 = dbc.Container([
    dbc.Row([
        dbc.Col(html.Div(id="kpi-brecha-saber"), md=3),
        dbc.Col(html.Div(id="kpi-brecha-internet"), md=3),
        dbc.Col(html.Div(id="kpi-brecha-pc"), md=3),
        dbc.Col(html.Div(id="kpi-cobertura"), md=3),
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="mapa-departamental"), md=6),
        dbc.Col(dcc.Graph(id="bar-areas-saber"), md=6),
    ]),
], fluid=True)

tab2 = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-ranking-deptos"), md=6),
        dbc.Col(dcc.Graph(id="bar-matricula-nivel"), md=6),
    ]),
    dbc.Row([dbc.Col(dcc.Graph(id="heatmap-depto-nivel"), md=12)]),
], fluid=True)

tab3 = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-estrato-zona"), md=6),
        dbc.Col(dcc.Graph(id="scatter-estrato-puntaje"), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-educacion-madre"), md=8),
        dbc.Col(html.Div(id="kpi-estrato1-rural"), md=4),
    ]),
], fluid=True)

tab4 = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Graph(id="gauge-internet"), md=4),
        dbc.Col(dcc.Graph(id="gauge-computador"), md=4),
        dbc.Col(dcc.Graph(id="bar-desercion-sena"), md=4),
    ]),
    dbc.Alert(
        "⚠️ Los datos de deserción SENA NO responden al filtro de Departamento, "
        "ya que el SENA opera con 33 Regionales que no se corresponden 1:1 con los departamentos del DANE.",
        color="warning", className="mt-2"
    ),
    dbc.Row([dbc.Col(dcc.Graph(id="combo-internet-puntaje"), md=12)]),
    html.H5("Índice de Priorización Departamental (Top 20)", className="mt-3"),
    html.P("Combina déficit académico (60%) + déficit de conectividad (40%).",
          className="text-muted"),
    dbc.Row([dbc.Col(html.Div(id="tabla-priorizacion"), md=12)]),
], fluid=True)

app.layout = dbc.Container([
    header, filtros,
    dbc.Tabs([
        dbc.Tab(tab1, label="📊 Panorama Ejecutivo"),
        dbc.Tab(tab2, label="🗺 Análisis Departamental y Nivel"),
        dbc.Tab(tab3, label="💰 Estratos y Capital Cultural"),
        dbc.Tab(tab4, label="📶 Brecha Digital y Priorización"),
    ]),
    footer,
], fluid=True)

# ============================================================
# 8. CALLBACK PRINCIPAL
# ============================================================
@app.callback(
    [Output("kpi-brecha-saber", "children"),
     Output("kpi-brecha-internet", "children"),
     Output("kpi-brecha-pc", "children"),
     Output("kpi-cobertura", "children"),
     Output("mapa-departamental", "figure"),
     Output("bar-areas-saber", "figure"),
     Output("bar-ranking-deptos", "figure"),
     Output("bar-matricula-nivel", "figure"),
     Output("heatmap-depto-nivel", "figure"),
     Output("bar-estrato-zona", "figure"),
     Output("scatter-estrato-puntaje", "figure"),
     Output("bar-educacion-madre", "figure"),
     Output("kpi-estrato1-rural", "children"),
     Output("gauge-internet", "figure"),
     Output("gauge-computador", "figure"),
     Output("bar-desercion-sena", "figure"),
     Output("combo-internet-puntaje", "figure"),
     Output("tabla-priorizacion", "children")],
    [Input("filtro-depto", "value"),
     Input("filtro-zona", "value"),
     Input("filtro-estrato", "value")]
)
def actualizar(deptos, zona, estratos):
    df = filtrar_saber11(deptos, zona, estratos)
    empty = fig_vacia("Sin datos en la selección")
    if df.empty or "punt_global" not in df.columns:
        empty_kpi = kpi_card("Sin datos", "—", COLOR_NEUTRO)
        return (empty_kpi,) * 4 + (empty,) * 5 + (empty,) * 3 + (empty_kpi,) + (empty,) * 4 + (html.Div("Sin datos"),)

    # ===== KPIs =====
    df_urb = df[df["Zona_Clean"] == "Urbano"]
    df_rur = df[df["Zona_Clean"] == "Rural"]

    p_urb = df_urb["punt_global"].mean() if not df_urb.empty else np.nan
    p_rur = df_rur["punt_global"].mean() if not df_rur.empty else np.nan
    brecha_saber = (p_urb - p_rur) if not (np.isnan(p_urb) or np.isnan(p_rur)) else 0

    int_urb = df_urb["Tiene_Internet"].mean() * 100 if not df_urb.empty and "Tiene_Internet" in df.columns else 0
    int_rur = df_rur["Tiene_Internet"].mean() * 100 if not df_rur.empty and "Tiene_Internet" in df.columns else 0
    brecha_int = int_urb - int_rur

    pc_urb = df_urb["Tiene_Computador"].mean() * 100 if not df_urb.empty and "Tiene_Computador" in df.columns else 0
    pc_rur = df_rur["Tiene_Computador"].mean() * 100 if not df_rur.empty and "Tiene_Computador" in df.columns else 0
    brecha_pc = pc_urb - pc_rur

    pct_rural = (df["Zona_Clean"] == "Rural").mean() * 100

    kpi1 = kpi_card("Brecha Saber 11", f"{brecha_saber:.1f}", COLOR_PDET, "puntos (Urb − Rur)")
    kpi2 = kpi_card("Brecha Internet", f"{brecha_int:.1f} pp", COLOR_RURAL, "puntos porcentuales")
    kpi3 = kpi_card("Brecha Computador", f"{brecha_pc:.1f} pp", COLOR_ACCENT, "puntos porcentuales")
    kpi4 = kpi_card("% Rural en muestra", f"{pct_rural:.1f}%", COLOR_PROMEDIO, "")

    # ===== TAB 1: mapa (barras como proxy) + barras áreas =====
    if "cole_depto_ubicacion" in df.columns and not df_rur.empty:
        df_depto = (df_rur.groupby("cole_depto_ubicacion")["punt_global"]
                    .mean().reset_index().sort_values("punt_global"))
        fig_mapa = px.bar(df_depto, y="cole_depto_ubicacion", x="punt_global",
                         orientation="h", title="Puntaje Rural Saber 11 por Departamento",
                         color="punt_global",
                         color_continuous_scale=[(0, COLOR_PDET), (0.5, COLOR_RURAL), (1, COLOR_PROMEDIO)],
                         labels={"cole_depto_ubicacion": "Departamento", "punt_global": "Puntaje"})
        fig_mapa.update_layout(height=600, showlegend=False)
    else:
        fig_mapa = empty

    areas = ["punt_matematicas", "punt_lectura_critica", "punt_sociales_ciudadanas",
             "punt_c_naturales", "punt_ingles"]
    areas_disp = [a for a in areas if a in df.columns]
    if areas_disp and "Zona_Clean" in df.columns:
        for a in areas_disp:
            df[a] = pd.to_numeric(df[a], errors="coerce")
        df_areas = df.groupby("Zona_Clean")[areas_disp].mean().reset_index()
        df_areas_m = df_areas.melt(id_vars="Zona_Clean", var_name="Área", value_name="Puntaje")
        df_areas_m["Área"] = df_areas_m["Área"].str.replace("punt_", "").str.title()
        fig_areas = px.bar(df_areas_m, x="Área", y="Puntaje", color="Zona_Clean",
                          barmode="group", color_discrete_map=PALETTE_ZONA,
                          title="Puntajes por Área: Urbano vs Rural")
        fig_areas.update_layout(height=400)
    else:
        fig_areas = empty

    # ===== TAB 2: Ranking + matricula por nivel + heatmap =====
    if "cole_depto_ubicacion" in df.columns and not df_rur.empty:
        df_rank = (df_rur.groupby("cole_depto_ubicacion")["punt_global"]
                   .mean().reset_index().sort_values("punt_global"))
        q70 = df_rank["punt_global"].quantile(0.7)
        q30 = df_rank["punt_global"].quantile(0.3)
        df_rank["Categoría"] = df_rank["punt_global"].apply(
            lambda x: "Top" if x >= q70 else ("Bottom" if x <= q30 else "Medio"))
        fig_rank = px.bar(df_rank, y="cole_depto_ubicacion", x="punt_global",
                         color="Categoría", orientation="h",
                         color_discrete_map={"Top": COLOR_PROMEDIO, "Medio": COLOR_NEUTRO, "Bottom": COLOR_PDET},
                         title="Ranking Departamental — Puntaje Rural Saber 11")
        fig_rank.update_layout(height=500)
    else:
        fig_rank = empty

    # Matricula por nivel educativo (columnas: tecnica_profesional, tecnologica, universitaria, etc.)
    if not df_matricula.empty:
        nivel_cols = [c for c in ["tecnica_profesional", "tecnologica", "universitaria",
                                   "especializacion", "maestria", "doctorado"]
                     if c in df_matricula.columns]
        if nivel_cols:
            for c in nivel_cols:
                df_matricula[c] = pd.to_numeric(df_matricula[c], errors="coerce")
            total_por_nivel = df_matricula[nivel_cols].sum().reset_index()
            total_por_nivel.columns = ["Nivel", "Matriculados"]
            total_por_nivel["Nivel"] = total_por_nivel["Nivel"].str.replace("_", " ").str.title()
            fig_nivel = px.bar(total_por_nivel, x="Nivel", y="Matriculados",
                              title="Matrícula Total por Nivel Educativo Superior",
                              color="Matriculados", color_continuous_scale="Blues")
            fig_nivel.update_layout(height=400)
        else:
            fig_nivel = empty
    else:
        fig_nivel = empty

    # Heatmap depto x nivel
    if not df_matricula.empty and "nombre_del_departamento" in df_matricula.columns:
        nivel_cols = [c for c in ["tecnica_profesional", "tecnologica", "universitaria",
                                   "especializacion", "maestria", "doctorado"]
                     if c in df_matricula.columns]
        if nivel_cols:
            df_heat = (df_matricula.groupby("nombre_del_departamento")[nivel_cols]
                      .sum().head(20))
            df_heat.columns = [c.replace("_", " ").title() for c in df_heat.columns]
            fig_heat = px.imshow(df_heat.T, color_continuous_scale="YlOrRd",
                                title="Matrícula por Departamento × Nivel (Top 20 deptos)",
                                aspect="auto")
            fig_heat.update_layout(height=400)
        else:
            fig_heat = empty
    else:
        fig_heat = empty

    # ===== TAB 3: Estratos =====
    if "Estrato_Num" in df.columns and "Zona_Clean" in df.columns:
        df_est = (df.dropna(subset=["Estrato_Num"])
                  .groupby(["Zona_Clean", "Estrato_Num"]).size().reset_index(name="Estudiantes"))
        df_est_total = df_est.groupby("Zona_Clean")["Estudiantes"].transform("sum")
        df_est["Porcentaje"] = df_est["Estudiantes"] / df_est_total * 100
        df_est["Estrato"] = "E" + df_est["Estrato_Num"].astype(int).astype(str)
        fig_est = px.bar(df_est, x="Zona_Clean", y="Porcentaje", color="Estrato",
                        title="Distribución de Estratos por Zona (%)",
                        color_discrete_sequence=px.colors.sequential.Viridis)
        fig_est.update_layout(height=400)
    else:
        fig_est = empty

    # Scatter estrato vs puntaje con tendencia manual (sin statsmodels)
    if "Estrato_Num" in df.columns:
        df_sc = (df.dropna(subset=["Estrato_Num", "punt_global"])
                .groupby(["Estrato_Num", "Zona_Clean"])["punt_global"].mean().reset_index())
        fig_scatter = go.Figure()
        for zona_val, color in PALETTE_ZONA.items():
            sub = df_sc[df_sc["Zona_Clean"] == zona_val]
            if len(sub) >= 2:
                fig_scatter.add_trace(go.Scatter(
                    x=sub["Estrato_Num"], y=sub["punt_global"],
                    mode="markers+lines", name=zona_val,
                    marker={"size": 12, "color": color}))
        fig_scatter.update_layout(title="Puntaje vs Estrato Socioeconómico",
                                 xaxis_title="Estrato", yaxis_title="Puntaje Promedio",
                                 height=400)
    else:
        fig_scatter = empty

    # Educación madre rural
    if "fami_educacionmadre" in df.columns and not df_rur.empty:
        df_madre = df_rur["fami_educacionmadre"].value_counts(normalize=True).head(10).reset_index()
        df_madre.columns = ["Nivel", "Porcentaje"]
        df_madre["Porcentaje"] = df_madre["Porcentaje"] * 100
        fig_madre = px.bar(df_madre, x="Porcentaje", y="Nivel", orientation="h",
                          title="Educación de la Madre (estudiantes rurales)",
                          color="Porcentaje", color_continuous_scale="Oranges")
        fig_madre.update_layout(height=400)
    else:
        fig_madre = empty

    # KPI E1 rural
    if not df_rur.empty and "Estrato_Num" in df_rur.columns:
        pct_e1 = (df_rur["Estrato_Num"] == 1).mean() * 100
    else:
        pct_e1 = 0
    kpi_e1 = kpi_card("% Rural en Estrato 1", f"{pct_e1:.1f}%", COLOR_PDET, "concentración socioeconómica")

    # ===== TAB 4: Gauges + Deserción + Combo + Priorización =====
    fig_g1 = go.Figure(go.Indicator(
        mode="gauge+number", value=int_rur,
        title={"text": "% Internet Rural"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": COLOR_RURAL},
               "steps": [{"range": [0, 30], "color": "#FFCDD2"},
                        {"range": [30, 60], "color": "#FFE0B2"},
                        {"range": [60, 100], "color": "#C8E6C9"}]}
    ))
    fig_g1.update_layout(height=300)

    fig_g2 = go.Figure(go.Indicator(
        mode="gauge+number", value=pc_rur,
        title={"text": "% Computador Rural"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": COLOR_ACCENT},
               "steps": [{"range": [0, 30], "color": "#FFCDD2"},
                        {"range": [30, 60], "color": "#FFE0B2"},
                        {"range": [60, 100], "color": "#C8E6C9"}]}
    ))
    fig_g2.update_layout(height=300)

    # Deserción SENA (isla de datos)
    if not df_sena_desercion.empty and "modalidad_formacion" in df_sena_desercion.columns:
        for c in ["total_aprendices_matriculados", "desertores_a_o_actual"]:
            if c in df_sena_desercion.columns:
                df_sena_desercion[c] = pd.to_numeric(df_sena_desercion[c], errors="coerce")
        if {"total_aprendices_matriculados", "desertores_a_o_actual"}.issubset(df_sena_desercion.columns):
            df_des = df_sena_desercion.groupby("modalidad_formacion").agg(
                matriculados=("total_aprendices_matriculados", "sum"),
                desertores=("desertores_a_o_actual", "sum")).reset_index()
            df_des["Tasa (%)"] = (df_des["desertores"] / df_des["matriculados"] * 100).round(2)
            df_des = df_des.sort_values("Tasa (%)", ascending=False)
            fig_des = px.bar(df_des, x="modalidad_formacion", y="Tasa (%)",
                            title="Deserción SENA por Modalidad",
                            color="Tasa (%)", color_continuous_scale=[(0, COLOR_PROMEDIO), (1, COLOR_PDET)],
                            text="Tasa (%)")
            fig_des.update_traces(textposition="outside")
            fig_des.update_layout(height=300, xaxis_title="Modalidad", showlegend=False)
        else:
            fig_des = empty
    else:
        fig_des = empty

    # Combo Internet rural + puntaje rural
    if "cole_depto_ubicacion" in df.columns and not df_rur.empty:
        df_combo = df_rur.groupby("cole_depto_ubicacion").agg(
            Internet=("Tiene_Internet", "mean"),
            Puntaje=("punt_global", "mean")).reset_index().sort_values("Puntaje")
        df_combo["Internet"] = df_combo["Internet"] * 100
        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(x=df_combo["cole_depto_ubicacion"], y=df_combo["Internet"],
                                  name="% Internet Rural", marker_color=COLOR_RURAL, yaxis="y"))
        fig_combo.add_trace(go.Scatter(x=df_combo["cole_depto_ubicacion"], y=df_combo["Puntaje"],
                                      name="Puntaje Rural", mode="lines+markers",
                                      marker_color=COLOR_BOGOTA, yaxis="y2"))
        fig_combo.update_layout(
            title="Conectividad e Internet vs Rendimiento Rural (Saber 11)",
            yaxis={"title": "% Internet Rural", "side": "left"},
            yaxis2={"title": "Puntaje Rural", "side": "right", "overlaying": "y"},
            xaxis={"tickangle": -45}, height=400, hovermode="x unified")
    else:
        fig_combo = empty

    # Tabla priorización
    if "cole_depto_ubicacion" in df.columns and not df_rur.empty:
        df_prio = df_rur.groupby("cole_depto_ubicacion").agg(
            Puntaje=("punt_global", "mean"),
            Internet=("Tiene_Internet", "mean")).reset_index()
        if len(df_prio) >= 2:
            p_min, p_max = df_prio["Puntaje"].min(), df_prio["Puntaje"].max()
            df_prio["Norm_Puntaje"] = 1 - (df_prio["Puntaje"] - p_min) / (p_max - p_min + 1e-9)
            df_prio["Norm_Internet"] = 1 - df_prio["Internet"]
            df_prio["Índice"] = (0.6 * df_prio["Norm_Puntaje"] + 0.4 * df_prio["Norm_Internet"]).round(3)
            df_show = df_prio.sort_values("Índice", ascending=False).head(20)[
                ["cole_depto_ubicacion", "Puntaje", "Internet", "Índice"]].copy()
            df_show.columns = ["Departamento", "Puntaje Rural", "% Internet Rural", "Índice"]
            df_show["Puntaje Rural"] = df_show["Puntaje Rural"].round(1)
            df_show["% Internet Rural"] = (df_show["% Internet Rural"] * 100).round(1)
            tabla = dash_table.DataTable(
                data=df_show.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df_show.columns],
                style_cell={"textAlign": "center", "fontFamily": "Segoe UI", "padding": "8px"},
                style_header={"backgroundColor": COLOR_BOGOTA, "color": "white", "fontWeight": "bold"},
                style_data_conditional=[
                    {"if": {"filter_query": "{Índice} > 0.7", "column_id": "Índice"},
                     "backgroundColor": "#FFCDD2", "color": COLOR_PDET, "fontWeight": "bold"}],
                page_size=20)
        else:
            tabla = html.Div("Datos insuficientes para el índice.")
    else:
        tabla = html.Div("Sin datos disponibles.")

    return (kpi1, kpi2, kpi3, kpi4,
            fig_mapa, fig_areas, fig_rank, fig_nivel, fig_heat,
            fig_est, fig_scatter, fig_madre, kpi_e1,
            fig_g1, fig_g2, fig_des, fig_combo, tabla)


# ============================================================
# 9. EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Iniciando dashboard en http://0.0.0.0:8050")
    print("=" * 70)
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
