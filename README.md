# 🎓 Dashboard Estratégico: Educación Rural en Colombia

Dashboard interactivo desarrollado en **Dash + Plotly** para visualizar las brechas educativas entre zonas rurales y urbanas de Colombia, integrando datos del DANE, ICFES, SENA y MEN.

> **Tercera entrega · Curso CSE10C2 Big Data · Universidad Piloto de Colombia · 2026**
> Profesor: Sergio David Díaz Veru

---

## 👥 Integrantes

- Daniel Leonardo Gómez Mora
- Karen Viviana Ávila Holguín
- Javier José Niño Ballesteros
- Juan Carlos Delgado Campuzano

---

## 📂 Estructura del proyecto

```
proyecto_dashboard/
├── app.py                          # Aplicación principal Dash
├── requirements.txt                # Dependencias Python
├── README_Dashboard_Dash.md        # Este archivo
└── data/                           # Carpeta de datos (crearla)
    ├── df_saber11_clean.csv
    ├── df_matricula_clean.csv
    ├── df_etdh_inst_clean.csv
    ├── df_etdh_prog_clean.csv
    ├── df_sena_cupos_clean.csv
    ├── df_sena_desercion_clean.csv
    └── DIVIPOLA-_Códigos_municipios_20250823.csv
```

---

## 🚀 Instalación local

### 1. Clonar el repositorio
```bash
git clone <tu-repo>
cd proyecto_dashboard
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Colocar los datos
Crea la carpeta `data/` y copia allí los 7 archivos CSV listos desde SharePoint.

### 5. Ejecutar el dashboard
```bash
python app.py
```

Abre tu navegador en **http://127.0.0.1:8050** 🎉

---

## 🎨 Características del dashboard

- **4 pestañas** organizadas por dimensión del problema:
  1. 📊 Panorama Ejecutivo (KPIs + mapa + barras Saber 11)
  2. 🗺 Análisis Departamental y por Nivel
  3. 💰 Estratos Socioeconómicos y Capital Cultural
  4. 📶 Brecha Digital y Priorización Municipal

- **Filtros globales sincronizados**: Departamento, Zona, Estrato (multi-select)
- **Índice de Priorización Municipal**: KPI compuesto (60% académico + 40% conectividad)
- **Paleta consistente**:
  - 🔵 Urbano (#2196F3)
  - 🟠 Rural (#FF9800)
  - 🔴 PDET/Crítico (#E53935)
  - 🟢 Promedio (#43A047)

---

## ☁️ Despliegue gratuito en la nube

### Opción 1: Render.com (RECOMENDADO)
1. Sube el código a GitHub.
2. Crea cuenta en https://render.com (gratis).
3. New → **Web Service** → conecta tu repo.
4. Configuración:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:server`
5. Render te da una URL pública del tipo `https://tu-app.onrender.com` ✅

### Opción 2: PythonAnywhere
1. Cuenta gratuita en https://www.pythonanywhere.com
2. Sube archivos vía web o git.
3. Configura el WSGI apuntando a `app.server`.

### Opción 3: Streamlit Community Cloud
> Nota: Dash no es nativo de Streamlit, pero puedes adaptar el código si prefieres esa plataforma.

### Opción 4: Hugging Face Spaces
1. Cuenta en https://huggingface.co
2. Crea un Space → tipo Docker o Gradio.
3. Sube el código → despliega gratis.

---

## 📊 Datos y fuentes

| Dataset | Registros | Fuente |
|---|---|---|
| Saber 11 | 50.000 | ICFES (datos.gov.co) |
| Matrícula | 19.618 | MEN |
| ETDH Instituciones | 3.976 | MEN |
| ETDH Programas | 19.867 | MEN |
| SENA Cupos | 42.080 | SENA |
| SENA Deserción | 42.080 | SENA |
| DIVIPOLA | 1.122 | DANE |
| **Total** | **177.621** | — |

---

## ⚠️ Notas técnicas

- La tabla `df_sena_desercion_clean` se modela como **isla de datos** porque el SENA opera con 33 Regionales que no coinciden 1:1 con los departamentos del DANE.
- Los filtros globales (Departamento) NO afectan los visuales de deserción SENA. Esto está documentado mediante un mensaje de alerta en la pestaña 4.
- El dataset Saber 11 es una muestra estratificada de 50.000 registros del universo total.

---

## 📜 Licencia

Este proyecto es académico, sin fines comerciales. Los datasets son de uso público bajo la política de Datos Abiertos del Estado colombiano.

---

## 🙏 Agradecimientos

- Portal de Datos Abiertos del Estado colombiano (datos.gov.co)
- Misión para la Transformación del Campo (DNP, 2015)
- Laboratorio de Economía de la Educación (LEE, Universidad Javeriana)
