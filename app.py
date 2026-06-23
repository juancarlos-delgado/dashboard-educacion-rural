"""
================================================================================
Dashboard Estratégico del Ecosistema de Educación Rural en Colombia
================================================================================
Tercera entrega - Curso Big Data
Universidad Piloto de Colombia - 2026
Profesor: Sergio David Díaz Veru

Integrantes:
- Daniel Leonardo Gómez Mora
- Karen Viviana Ávila Holguín
- Javier José Niño Ballesteros
- Juan Carlos Delgado Campuzano

Stack: Dash + Plotly + Bootstrap
Ejecutar: python app.py
================================================================================
"""

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table, no_update
import dash_bootstrap_components as dbc

# ============================================================
# 1. CONFIGURACIÓN DE COLORES Y CONSTANTES
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
# 2. CARGA DE DATOS (con manejo de errores)
# ============================================================
def cargar_csv(filename, **kwargs):
    """Carga un CSV desde la carpeta data/ con manejo de errores."""
    ruta = os.path.join(DATA_DIR, filename)
    try:
        df = pd.read_csv(ruta, low_memory=False, **kwargs)
        print(f"✓ {filename}: {len(df):,} filas")
        return df
    except FileNotFoundError:
        print(f"✗ ADVERTENCIA: No se encontró {ruta}")
        return pd.DataFrame()
    except Exception as e:
        print(f"✗ ERROR al cargar {filename}: {e}")
        return pd.DataFrame()

print("=" * 60)
print("Cargando datasets...")
print("=" * 60)

df_saber11 = cargar_csv("df_saber11_clean.csv")
df_matricula = cargar_csv("df_matricula_clean.csv")
df_etdh_inst = cargar_csv("df_etdh_inst_clean.csv")
df_etdh_prog = cargar_csv("df_etdh_prog_clean.csv")
df_sena_cupos = cargar_csv("df_sena_cupos_clean.csv")
df_sena_desercion = cargar_csv("df_sena_desercion_clean.csv")
df_divipola = cargar_csv("DIVIPOLA-_Códigos_municipios_20250823.csv")

# ============================================================
# 3. ENRIQUECIMIENTO DE COLUMNAS DERIVADAS
# ============================================================
if not df_saber11.empty:
    # Zona_Clean: normalizar URBANO/RURAL
    if "cole_area_ubicacion" in df_saber11.columns:
        df_saber11["Zona_Clean"] = np.where(
            df_saber11["cole_area_ubicacion"].astype(str).str.upper() == "URBANO",
            "Urbano", "Rural"
        )
    # Tiene_Internet
    if "fami_tieneinternet" in df_saber11.columns:
        df_saber11["Tiene_Internet"] = np.where(
            df_saber11["fami_tieneinternet"].astype(str).str.strip() == "Si", 1, 0
        )
    # Tiene_Computador
    if "fami_tienecomputador" in df_saber11.columns:
        df_saber11["Tiene_Computador"] = np.where(
            df_saber11["fami_tienecomputador"].astype(str).str.strip() == "Si", 1, 0
        )
    # Estrato_Num
    if "fami_estratovivienda" in df_saber11.columns:
        df_saber11["Estrato_Num"] = (
            df_saber11["fami_estratovivienda"].astype(str)
            .str.extract(r"(\d+)").astype(float)
        )

# ============================================================
# 4. FUNCIONES AUXILIARES
# ============================================================
def filtrar_saber11(departamentos, zona, estratos):
    """Aplica los filtros globales al dataset Saber11."""
    df = df_saber11.copy()
    if departamentos and "cole_depto_ubicacion" in df.columns:
        df = df[df["cole_depto_ubicacion"].isin(departamentos)]
    if zona and "Zona_Clean" in df.columns:
        df = df[df["Zona_Clean"].isin(zona)]
    if estratos and "Estrato_Num" in df.columns:
        df = df[df["Estrato_Num"].isin(estratos)]
    return df

def kpi_card(titulo, valor, color, subtitulo=""):
    """Tarjeta KPI con borde de color."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(titulo, className="text-muted mb-1", style={"fontSize": "12px"}),
            html.H2(valor, className="mb-0", style={"color": color, "fontWeight": "bold"}),
            html.Small(subtitulo, className="text-muted") if subtitulo else None,
        ]),
        style={
            "borderLeft": f"5px solid {color}",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"
        }
    )

# ============================================================
# 5. INICIALIZACIÓN DE LA APP
# ============================================================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Dashboard Educación Rural"
)
server = app.server  # para despliegue en Render/Heroku

# Listas para filtros
deptos_disponibles = []
if not df_saber11.empty and "cole_depto_ubicacion" in df_saber11.columns:
    deptos_disponibles = sorted(df_saber11["cole_depto_ubicacion"].dropna().unique())

# ============================================================
# 6. LAYOUT GLOBAL
# ============================================================
header = dbc.Container([
    html.Div([
        html.H2(
            "Dashboard Estratégico: Educación Rural en Colombia",
            style={"color": "white", "marginBottom": "0"}
        ),
        html.P(
            "Universidad Piloto de Colombia · CSE10C2 Big Data · 2026",
            style={"color": "#E3F2FD", "marginBottom": "0"}
        ),
    ], style={
        "background": f"linear-gradient(135deg, {COLOR_BOGOTA} 0%, {COLOR_URBANO} 100%)",
        "padding": "20px 30px",
        "borderRadius": "0 0 10px 10px",
        "marginBottom": "20px"
    })
], fluid=True)

filtros = dbc.Card(dbc.CardBody([
    dbc.Row([
        dbc.Col([
            html.Label("Departamento", className="fw-bold"),
            dcc.Dropdown(
                id="filtro-depto",
                options=[{"label": d, "value": d} for d in deptos_disponibles],
                multi=True,
                placeholder="Todos los departamentos",
            )
        ], md=5),
        dbc.Col([
            html.Label("Zona", className="fw-bold"),
            dcc.Dropdown(
                id="filtro-zona",
                options=[
                    {"label": "Urbano", "value": "Urbano"},
                    {"label": "Rural", "value": "Rural"}
                ],
                multi=True,
                placeholder="Ambas zonas",
            )
        ], md=3),
        dbc.Col([
            html.Label("Estrato", className="fw-bold"),
            dcc.Dropdown(
                id="filtro-estrato",
                options=[{"label": f"Estrato {i}", "value": i} for i in range(1, 7)],
                multi=True,
                placeholder="Todos los estratos",
            )
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

# ----- TAB 1 -----
tab1_layout = dbc.Container([
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

# ----- TAB 2 -----
tab2_layout = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-ranking-deptos"), md=6),
        dbc.Col(dcc.Graph(id="bar-matricula-nivel"), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="heatmap-depto-nivel"), md=12),
    ]),
], fluid=True)

# ----- TAB 3 -----
tab3_layout = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-estrato-zona"), md=6),
        dbc.Col(dcc.Graph(id="scatter-estrato-puntaje"), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-educacion-madre"), md=8),
        dbc.Col(html.Div(id="kpi-estrato1-rural"), md=4),
    ]),
], fluid=True)

# ----- TAB 4 -----
tab4_layout = dbc.Container([
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
    dbc.Row([
        dbc.Col(dcc.Graph(id="combo-internet-puntaje"), md=12),
    ]),
    html.H5("Índice de Priorización Municipal (Top 20)", className="mt-3"),
    html.P("Combina déficit académico (60%) + déficit de conectividad (40%).", className="text-muted"),
    dbc.Row([
        dbc.Col(html.Div(id="tabla-priorizacion"), md=12),
    ]),
], fluid=True)

app.layout = dbc.Container([
    header,
    filtros,
    dbc.Tabs([
        dbc.Tab(tab1_layout, label="📊 Panorama Ejecutivo"),
        dbc.Tab(tab2_layout, label="🗺 Análisis Departamental y Nivel"),
        dbc.Tab(tab3_layout, label="💰 Estratos y Capital Cultural"),
        dbc.Tab(tab4_layout, label="📶 Brecha Digital y Priorización"),
    ]),
    footer,
], fluid=True)

# ============================================================
# 7. CALLBACKS
# ============================================================
@app.callback(
    [
        Output("kpi-brecha-saber", "children"),
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
        Output("tabla-priorizacion", "children"),
    ],
    [
        Input("filtro-depto", "value"),
        Input("filtro-zona", "value"),
        Input("filtro-estrato", "value"),
    ]
)
def actualizar_dashboard(deptos, zona, estratos):
    df = filtrar_saber11(deptos, zona, estratos)

    # ---- KPIs ----
    if df.empty:
        empty_fig = go.Figure().add_annotation(text="Sin datos para filtros seleccionados",
                                                xref="paper", yref="paper", showarrow=False)
        empty_kpi = kpi_card("Sin datos", "—", COLOR_NEUTRO)
        return (empty_kpi, empty_kpi, empty_kpi, empty_kpi,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_fig, empty_kpi,
                empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("Sin datos"))

    # Brecha Saber 11
    p_urbano = df[df["Zona_Clean"] == "Urbano"]["punt_global"].mean()
    p_rural = df[df["Zona_Clean"] == "Rural"]["punt_global"].mean()
    brecha_saber = (p_urbano - p_rural) if not np.isnan(p_urbano) and not np.isnan(p_rural) else 0

    # Brecha Internet
    int_urb = df[df["Zona_Clean"] == "Urbano"]["Tiene_Internet"].mean() * 100
    int_rur = df[df["Zona_Clean"] == "Rural"]["Tiene_Internet"].mean() * 100
    brecha_int = int_urb - int_rur if not np.isnan(int_urb) and not np.isnan(int_rur) else 0

    # Brecha Computador
    pc_urb = df[df["Zona_Clean"] == "Urbano"]["Tiene_Computador"].mean() * 100
    pc_rur = df[df["Zona_Clean"] == "Rural"]["Tiene_Computador"].mean() * 100
    brecha_pc = pc_urb - pc_rur if not np.isnan(pc_urb) and not np.isnan(pc_rur) else 0

    # Cobertura rural (% de la muestra que es rural)
    cobertura_rural = (df["Zona_Clean"] == "Rural").mean() * 100

    kpi1 = kpi_card("Brecha Saber 11", f"{brecha_saber:.1f}", COLOR_PDET, "puntos (Urb − Rur)")
    kpi2 = kpi_card("Brecha Internet", f"{brecha_int:.1f} pp", COLOR_RURAL, "puntos porcentuales")
    kpi3 = kpi_card("Brecha Computador", f"{brecha_pc:.1f} pp", COLOR_ACCENT, "puntos porcentuales")
    kpi4 = kpi_card("% Rural en muestra", f"{cobertura_rural:.1f}%", COLOR_PROMEDIO, "")

    # ---- TAB 1: Mapa departamental (barras como fallback) ----
    df_depto = (df[df["Zona_Clean"] == "Rural"]
                .groupby("cole_depto_ubicacion")["punt_global"].mean()
                .reset_index().sort_values("punt_global"))
    fig_mapa = px.bar(df_depto, y="cole_depto_ubicacion", x="punt_global",
                     orientation="h", title="Puntaje Rural Saber 11 por Departamento",
                     color="punt_global", color_continuous_scale=[(0, COLOR_PDET), (0.5, COLOR_RURAL), (1, COLOR_PROMEDIO)],
                     labels={"cole_depto_ubicacion": "Departamento", "punt_global": "Puntaje promedio"})
    fig_mapa.update_layout(height=600, showlegend=False)

    # Barras por áreas Saber 11
    areas = ["punt_matematicas", "punt_lectura_critica", "punt_sociales_ciudadanas",
             "punt_c_naturales", "punt_ingles"]
    areas_disponibles = [a for a in areas if a in df.columns]
    df_areas = df.groupby("Zona_Clean")[areas_disponibles].mean().reset_index()
    df_areas_m = df_areas.melt(id_vars="Zona_Clean", var_name="Área", value_name="Puntaje")
    df_areas_m["Área"] = df_areas_m["Área"].str.replace("punt_", "").str.title()
    fig_areas = px.bar(df_areas_m, x="Área", y="Puntaje", color="Zona_Clean",
                       barmode="group", color_discrete_map=PALETTE_ZONA,
                       title="Puntajes por Área: Urbano vs Rural")
    fig_areas.update_layout(height=400)

    # ---- TAB 2: Ranking departamentos ----
    df_rank = df_depto.copy()
    df_rank["Categoría"] = "Medio"
    df_rank.loc[df_rank["punt_global"] >= df_rank["punt_global"].quantile(0.7), "Categoría"] = "Top"
    df_rank.loc[df_rank["punt_global"] <= df_rank["punt_global"].quantile(0.3), "Categoría"] = "Bottom"
    fig_rank = px.bar(df_rank.sort_values("punt_global"), y="cole_depto_ubicacion", x="punt_global",
                      color="Categoría", orientation="h",
                      color_discrete_map={"Top": COLOR_PROMEDIO, "Medio": COLOR_NEUTRO, "Bottom": COLOR_PDET},
                      title="Ranking Departamental — Puntaje Rural Saber 11")
    fig_rank.update_layout(height=500)

    # Matrícula por nivel
    if not df_matricula.empty and "zona" in df_matricula.columns:
        nivel_cols = [c for c in ["doctorado","especializacion","ies_con_oferta","maestria","tecnica_profesional","tecnologica","universitaria"] if c in df_matricula.columns]
        if nivel_cols:
            df_niv = df_matricula.groupby("zona")[nivel_cols].sum().reset_index()
            df_niv_m = df_niv.melt(id_vars="zona", var_name="Nivel", value_name="Matriculados")
            fig_nivel = px.bar(df_niv_m, x="Nivel", y="Matriculados", color="zona", barmode="group",
                              title="Matrícula por Nivel y Zona")
        else:
            fig_nivel = go.Figure().add_annotation(text="Sin columnas de nivel", showarrow=False)
    else:
        fig_nivel = go.Figure().add_annotation(text="df_matricula no disponible", showarrow=False)
    fig_nivel.update_layout(height=400)

    # Heatmap departamento × nivel (usa matrícula)
    if not df_matricula.empty and "c_digo_deldepartamento" in df_matricula.columns:
        df_heat = df_matricula.groupby("c_digo_deldepartamento")[nivel_cols].sum().head(15) if nivel_cols else pd.DataFrame()
        if not df_heat.empty:
            fig_heat = px.imshow(df_heat.T, color_continuous_scale="YlOrRd",
                                title="Heatmap: Matrícula por Departamento × Nivel")
        else:
            fig_heat = go.Figure().add_annotation(text="Sin datos para heatmap", showarrow=False)
    else:
        fig_heat = go.Figure().add_annotation(text="df_matricula no disponible", showarrow=False)
    fig_heat.update_layout(height=400)

    # ---- TAB 3: Estratos ----
    if "Estrato_Num" in df.columns:
        df_est = (df.groupby(["Zona_Clean", "Estrato_Num"]).size()
                  .reset_index(name="Estudiantes"))
        df_est_total = df_est.groupby("Zona_Clean")["Estudiantes"].transform("sum")
        df_est["Porcentaje"] = df_est["Estudiantes"] / df_est_total * 100
        fig_est = px.bar(df_est, x="Zona_Clean", y="Porcentaje", color="Estrato_Num",
                        title="Distribución de Estratos por Zona (%)",
                        color_continuous_scale="Viridis")
    else:
        fig_est = go.Figure()
    fig_est.update_layout(height=400)

    # Scatter estrato vs puntaje
    if "Estrato_Num" in df.columns:
        df_sc = df.dropna(subset=["Estrato_Num", "punt_global"]).copy()
        df_sc_agg = df_sc.groupby(["Estrato_Num","Zona_Clean"])["punt_global"].mean().reset_index()
        fig_scatter = px.scatter(df_sc_agg, x="Estrato_Num", y="punt_global", color="Zona_Clean",
                                trendline="ols", color_discrete_map=PALETTE_ZONA,
                                title="Puntaje vs Estrato Socioeconómico", size_max=20)
    else:
        fig_scatter = go.Figure()
    fig_scatter.update_layout(height=400)

    # Educación de la madre (rural)
    if "fami_educacionmadre" in df.columns:
        df_madre = df[df["Zona_Clean"] == "Rural"]["fami_educacionmadre"].value_counts(normalize=True).reset_index()
        df_madre.columns = ["Nivel", "Porcentaje"]
        df_madre["Porcentaje"] = df_madre["Porcentaje"] * 100
        fig_madre = px.bar(df_madre.head(10), x="Porcentaje", y="Nivel", orientation="h",
                          title="Educación de la Madre (estudiantes rurales)",
                          color="Porcentaje", color_continuous_scale="Oranges")
    else:
        fig_madre = go.Figure()
    fig_madre.update_layout(height=400)

    # KPI Estrato 1 rural
    rural_df = df[df["Zona_Clean"] == "Rural"]
    if not rural_df.empty and "Estrato_Num" in rural_df.columns:
        pct_e1 = (rural_df["Estrato_Num"] == 1).mean() * 100
    else:
        pct_e1 = 0
    kpi_e1 = kpi_card("% Rural en Estrato 1", f"{pct_e1:.1f}%", COLOR_PDET,
                      "concentración socioeconómica")

    # ---- TAB 4: Brecha digital ----
    # Gauges
    fig_g1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=int_rur,
        title={"text": "% Internet Rural"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": COLOR_RURAL},
            "steps": [
                {"range": [0, 30], "color": "#FFCDD2"},
                {"range": [30, 60], "color": "#FFE0B2"},
                {"range": [60, 100], "color": "#C8E6C9"},
            ],
            "threshold": {"line": {"color": COLOR_PDET, "width": 4}, "thickness": 0.75, "value": 50}
        }
    ))
    fig_g1.update_layout(height=300)

    fig_g2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pc_rur,
        title={"text": "% Computador Rural"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": COLOR_ACCENT},
            "steps": [
                {"range": [0, 30], "color": "#FFCDD2"},
                {"range": [30, 60], "color": "#FFE0B2"},
                {"range": [60, 100], "color": "#C8E6C9"},
            ],
            "threshold": {"line": {"color": COLOR_PDET, "width": 4}, "thickness": 0.75, "value": 50}
        }
    ))
    fig_g2.update_layout(height=300)

    # Deserción SENA (isla de datos — NO se filtra por departamento)
    if not df_sena_desercion.empty and "modalidad_formacion" in df_sena_desercion.columns:
        col_mat = "total_aprendices_matriculados" if "total_aprendices_matriculados" in df_sena_desercion.columns else None
        col_des = "desertores_a_o_actual" if "desertores_a_o_actual" in df_sena_desercion.columns else None
        if col_mat and col_des:
            df_des = df_sena_desercion.groupby("modalidad_formacion").agg(
                matriculados=(col_mat, "sum"),
                desertores=(col_des, "sum")
            ).reset_index()
            df_des["Tasa (%)"] = df_des["desertores"] / df_des["matriculados"] * 100
            fig_des = px.bar(df_des.sort_values("Tasa (%)", ascending=False),
                            x="modalidad_formacion", y="Tasa (%)",
                            title="Deserción SENA por Modalidad",
                            color="Tasa (%)", color_continuous_scale=[(0, COLOR_PROMEDIO), (1, COLOR_PDET)])
        else:
            fig_des = go.Figure().add_annotation(text="Columnas SENA no encontradas", showarrow=False)
    else:
        fig_des = go.Figure().add_annotation(text="df_sena_desercion no disponible", showarrow=False)
    fig_des.update_layout(height=300)

    # Combo: Internet rural + puntaje rural por departamento
    df_combo = df[df["Zona_Clean"] == "Rural"].groupby("cole_depto_ubicacion").agg(
        Internet=("Tiene_Internet", "mean"),
        Puntaje=("punt_global", "mean")
    ).reset_index().sort_values("Puntaje")
    df_combo["Internet"] = df_combo["Internet"] * 100

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(x=df_combo["cole_depto_ubicacion"], y=df_combo["Internet"],
                              name="% Internet Rural", marker_color=COLOR_RURAL, yaxis="y"))
    fig_combo.add_trace(go.Scatter(x=df_combo["cole_depto_ubicacion"], y=df_combo["Puntaje"],
                                   name="Puntaje Rural", mode="lines+markers",
                                   marker_color=COLOR_BOGOTA, yaxis="y2"))
    fig_combo.update_layout(
        title="Correlación: Conectividad e Internet vs Rendimiento Rural (Saber 11)",
        yaxis=dict(title="% Internet Rural", side="left"),
        yaxis2=dict(title="Puntaje Rural", side="right", overlaying="y"),
        xaxis=dict(tickangle=-45),
        height=400, hovermode="x unified"
    )

    # Tabla de priorización
    df_prio = df[df["Zona_Clean"] == "Rural"].groupby("cole_depto_ubicacion").agg(
        Puntaje=("punt_global", "mean"),
        Internet=("Tiene_Internet", "mean")
    ).reset_index()
    if not df_prio.empty:
        p_min = df_prio["Puntaje"].min()
        p_max = df_prio["Puntaje"].max()
        df_prio["Norm_Puntaje"] = 1 - (df_prio["Puntaje"] - p_min) / (p_max - p_min + 1e-9)
        df_prio["Norm_Internet"] = 1 - df_prio["Internet"]
        df_prio["Índice"] = 0.6 * df_prio["Norm_Puntaje"] + 0.4 * df_prio["Norm_Internet"]
        df_prio = df_prio.sort_values("Índice", ascending=False).head(20)
        df_prio_display = df_prio[["cole_depto_ubicacion", "Puntaje", "Internet", "Índice"]].copy()
        df_prio_display.columns = ["Departamento", "Puntaje Rural", "% Internet Rural", "Índice"]
        df_prio_display["Puntaje Rural"] = df_prio_display["Puntaje Rural"].round(1)
        df_prio_display["% Internet Rural"] = (df_prio_display["% Internet Rural"] * 100).round(1)
        df_prio_display["Índice"] = df_prio_display["Índice"].round(3)
        tabla = dash_table.DataTable(
            data=df_prio_display.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_prio_display.columns],
            style_cell={"textAlign": "center", "fontFamily": "Segoe UI", "padding": "8px"},
            style_header={"backgroundColor": COLOR_BOGOTA, "color": "white", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"filter_query": "{Índice} > 0.7", "column_id": "Índice"},
                 "backgroundColor": "#FFCDD2", "color": COLOR_PDET, "fontWeight": "bold"}
            ],
            page_size=20
        )
    else:
        tabla = html.Div("Sin datos")

    return (kpi1, kpi2, kpi3, kpi4,
            fig_mapa, fig_areas, fig_rank, fig_nivel, fig_heat,
            fig_est, fig_scatter, fig_madre, kpi_e1,
            fig_g1, fig_g2, fig_des, fig_combo, tabla)


# ============================================================
# 8. EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Iniciando dashboard en http://127.0.0.1:8050")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=8050)
