import streamlit as st
import pandas as pd
import json
from streamlit_extras import local_storage_manager

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(page_title="Notas", layout="wide", page_icon="🎓")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* Fondo oscuro general */
.stApp {
    background-color: #0f1117 !important;
    color: #e2e2e8 !important;
}

/* Todos los textos en modo oscuro */
.stApp p, .stApp span, .stApp label, .stApp div,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    color: #e2e2e8 !important;
}

/* Sidebar oscuro marino */
[data-testid="stSidebar"] {
    background-color: #1a1a2e !important;
}
[data-testid="stSidebar"] * {
    color: #c8c8d8 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid #2d2d4e !important;
    color: #c8c8d8 !important;
    border-radius: 6px;
    font-size: 0.85rem;
    text-align: left;
    transition: all 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2d2d4e !important;
    border-color: #5b5bab !important;
    color: #ffffff !important;
}

/* Inputs dentro del sidebar */
[data-testid="stSidebar"] input {
    background: #2d2d4e !important;
    color: #e2e2e8 !important;
    border: 1px solid #3d3d6e !important;
}

/* Contenido principal */
[data-testid="stMain"] {
    background-color: #0f1117 !important;
}
[data-testid="block-container"] {
    background-color: #0f1117 !important;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #2d2d4e !important;
    border-radius: 10px !important;
    background: #161b2e !important;
    margin-bottom: 12px !important;
}
[data-testid="stExpander"] summary {
    color: #e2e2e8 !important;
}

/* Data editor oscuro */
[data-testid="stDataEditor"] {
    border-radius: 8px !important;
    overflow: hidden;
}
[data-testid="stDataEditor"] * {
    background-color: #1a1f35 !important;
    color: #e2e2e8 !important;
}

/* Métricas */
[data-testid="stMetric"] {
    background: #161b2e !important;
    border: 1px solid #2d2d4e !important;
    border-radius: 8px;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.75rem !important;
    color: #7c7ca8 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 1.4rem !important;
    color: #e2e2e8 !important;
}

/* Botón primario */
.stButton > button[kind="primary"] {
    background: #3b3bab !important;
    color: white !important;
    border: none !important;
    border-radius: 8px;
    font-weight: 500;
}
.stButton > button[kind="primary"]:hover {
    background: #5b5bcc !important;
}

/* Botón secundario */
.stButton > button {
    background: #1a1f35 !important;
    color: #c8c8d8 !important;
    border: 1px solid #2d2d4e !important;
    border-radius: 8px;
}
.stButton > button:hover {
    background: #2d2d4e !important;
    color: #ffffff !important;
}

/* Alerts */
.stAlert {
    background: #1a1f35 !important;
    border-radius: 8px !important;
}

/* Inputs generales */
input, textarea, select {
    background: #1a1f35 !important;
    color: #e2e2e8 !important;
    border: 1px solid #2d2d4e !important;
    border-radius: 6px !important;
}

/* Divider */
hr {
    border-color: #2d2d4e !important;
}

/* Caption */
.stApp .stCaption, .stApp small {
    color: #7c7ca8 !important;
}

/* Checkboxes, selectboxes */
[data-testid="stSelectbox"] > div,
[data-testid="stNumberInput"] > div {
    background: #1a1f35 !important;
}

/* Tags especiales */
.tag-special {
    display: inline-block;
    font-size: 0.68rem;
    padding: 1px 7px;
    border-radius: 4px;
    background: #2d1f5e;
    color: #a78bfa;
    font-weight: 500;
    margin-left: 6px;
    font-family: 'DM Mono', monospace;
}

/* Badge de estado */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    font-family: 'DM Mono', monospace;
}
.badge-ok      { background: #14532d; color: #86efac; }
.badge-warn    { background: #451a03; color: #fcd34d; }
.badge-bad     { background: #450a0a; color: #fca5a5; }
.badge-neutral { background: #1e2035; color: #7c7ca8; }

/* Auto-save chip */
.autosave-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    color: #7c7ca8;
    padding: 3px 10px;
    background: #1a1f35;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    border: 1px solid #2d2d4e;
}

/* Info box especial para reglas de cálculo */
.regla-box {
    background: #1a1f35;
    border: 1px solid #3b3bab;
    border-left: 3px solid #5b5bcc;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.82rem;
    color: #a78bfa;
    font-family: 'DM Mono', monospace;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  LOCAL STORAGE
# ─────────────────────────────────────────────
manager = local_storage_manager.LocalStorageManager(key="calculadora_notas_v3")
if not manager.ready():
    st.markdown("⏳ Cargando datos...")
    st.stop()

# ─────────────────────────────────────────────
#  MODELO DE DATOS
# ─────────────────────────────────────────────
# Grupo:
#   nombre: str
#   ponderacion: float          — peso en nota final del ramo (ignorado si usa avg_n a nivel ramo)
#   min_aprobacion: float|None  — mínimo independiente
#   es_reprobatorio: bool       — reprobar ramo si no cumple mínimo
#   mejores_n: int|None         — contar solo las N mejores notas DENTRO del grupo
#   peso_doble: bool            — este grupo entra dos veces en el AVG-N del ramo (ej: examen)
#   items: list[{Evaluación, Nota, Ponderación %}]
#
# Ramo:
#   grupos: list[Grupo]
#   avg_n_ramo: int|None  — si está definido, la NF = promedio de las avg_n_ramo mejores
#                           notas entre los grupos (considerando peso_doble)

def migrar_ramo(data):
    if isinstance(data, list):
        return {"avg_n_ramo": None, "grupos": [{
            "nombre": "General", "ponderacion": 100.0,
            "min_aprobacion": None, "es_reprobatorio": False,
            "mejores_n": None, "peso_doble": False, "items": data
        }]}
    data.setdefault("avg_n_ramo", None)
    for g in data.get("grupos", []):
        g.setdefault("es_reprobatorio", False)
        g.setdefault("mejores_n", None)
        g.setdefault("peso_doble", False)
    return data


def cargar_ramos():
    raw = manager.get("ramos_v3", None)
    if raw is None:
        for old_key in ["ramos_v2", "ramos"]:
            raw_old = manager.get(old_key, None)
            if raw_old:
                if isinstance(raw_old, str):
                    try: raw_old = json.loads(raw_old)
                    except: raw_old = {}
                return {k: migrar_ramo(v) for k, v in raw_old.items()}
        return {}
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except: return {}
    return {k: migrar_ramo(v) for k, v in raw.items()}


def guardar_ramos(ramos):
    manager.set("ramos_v3", ramos)


def ramo_nuevo():
    return {"avg_n_ramo": None, "grupos": [{
        "nombre": "General", "ponderacion": 100.0,
        "min_aprobacion": None, "es_reprobatorio": False,
        "mejores_n": None, "peso_doble": False, "items": []
    }]}


# ─────────────────────────────────────────────
#  CÁLCULO
# ─────────────────────────────────────────────
def calcular_grupo(grupo):
    """(nota, peso_completado)  — respeta mejores_n dentro del grupo."""
    items = grupo.get("items", [])
    validos = []
    for it in items:
        try:
            validos.append({"nota": float(it["Nota"]), "peso": float(it["Ponderación %"])})
        except (TypeError, ValueError, KeyError):
            pass

    mejores_n = grupo.get("mejores_n")
    if mejores_n and len(validos) > mejores_n:
        validos = sorted(validos, key=lambda x: x["nota"], reverse=True)[:mejores_n]
        suma_p = sum(i["peso"] for i in validos)
        if suma_p == 0:
            return None, 0.0
        nota = sum(i["nota"] * i["peso"] / suma_p for i in validos)
        return nota, 100.0

    if not validos:
        return None, 0.0
    nota = sum(i["nota"] * i["peso"] / 100 for i in validos)
    peso = sum(i["peso"] for i in validos)
    return nota, peso


def calcular_ramo(ramo_data):
    grupos = ramo_data.get("grupos", [])
    avg_n  = ramo_data.get("avg_n_ramo")
    aprobacion_ok = True
    detalle_grupos = []

    notas_grupos = []  # para avg_n_ramo
    nota_final   = 0.0
    peso_completado = 0.0

    for g in grupos:
        nota_g, peso_g = calcular_grupo(g)
        pond      = g.get("ponderacion", 0.0)
        min_ap    = g.get("min_aprobacion")
        es_repro  = g.get("es_reprobatorio", False)
        doble     = g.get("peso_doble", False)

        cumple = True
        if min_ap is not None and nota_g is not None:
            cumple = nota_g >= min_ap
        if not cumple and es_repro:
            aprobacion_ok = False

        # Construir lista para avg_n_ramo
        if nota_g is not None:
            notas_grupos.append(nota_g)
            if doble:
                notas_grupos.append(nota_g)  # entra dos veces

        contrib = 0.0
        if not avg_n and nota_g is not None:
            contrib = nota_g * (pond / 100)
            peso_completado += pond

        detalle_grupos.append({
            "nombre": g["nombre"], "nota": nota_g, "peso_g": peso_g,
            "ponderacion": pond, "min_ap": min_ap, "es_repro": es_repro,
            "cumple": cumple, "doble": doble, "contrib": contrib,
        })

    # Calcular nota final
    if avg_n:
        n_total_grupos = sum(2 if g.get("peso_doble") else 1 for g in grupos)
        if notas_grupos:
            tomar = min(avg_n, len(notas_grupos))
            mejores = sorted(notas_grupos, reverse=True)[:tomar]
            nota_final = sum(mejores) / tomar
            peso_completado = (len(notas_grupos) / n_total_grupos) * 100
    else:
        nota_final = sum(d["contrib"] for d in detalle_grupos)

    return {
        "nota_final": nota_final,
        "peso_completado": peso_completado,
        "aprobacion_ok": aprobacion_ok,
        "grupos": detalle_grupos,
        "avg_n_ramo": avg_n,
    }


# ─────────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────────
def badge(texto, tipo="neutral"):
    return f'<span class="badge badge-{tipo}">{texto}</span>'

def nota_color(nota, minimo=4.0):
    if nota is None: return "neutral"
    if nota >= minimo: return "ok"
    if nota >= 3.5:   return "warn"
    return "bad"


# ─────────────────────────────────────────────
#  ESTADO
# ─────────────────────────────────────────────
if "ramos" not in st.session_state:
    st.session_state.ramos = cargar_ramos()
if "ramo_sel" not in st.session_state:
    st.session_state.ramo_sel = None
if "modo" not in st.session_state:
    st.session_state.modo = "notas"


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 Mis Ramos")
    st.markdown("---")

    with st.expander("＋ Nuevo ramo"):
        nuevo = st.text_input("Nombre:", key="input_nuevo",
                              label_visibility="collapsed",
                              placeholder="Ej: Cálculo II").strip()
        if st.button("Crear", key="btn_crear"):
            if nuevo and nuevo not in st.session_state.ramos:
                st.session_state.ramos[nuevo] = ramo_nuevo()
                st.session_state.ramo_sel = nuevo
                st.session_state.modo = "notas"
                guardar_ramos(st.session_state.ramos)
                st.rerun()
            elif nuevo in st.session_state.ramos:
                st.warning("Ya existe.")

    st.markdown("---")
    for r in list(st.session_state.ramos.keys()):
        res  = calcular_ramo(st.session_state.ramos[r])
        nota_sb = f"  ·  {res['nota_final']:.1f}" if res["peso_completado"] > 0 else ""
        activo  = "▶ " if r == st.session_state.ramo_sel else ""
        if st.button(f"{activo}{r}{nota_sb}", key=f"sb_{r}", use_container_width=True):
            st.session_state.ramo_sel = r
            st.session_state.modo = "notas"
            st.rerun()


# ─────────────────────────────────────────────
#  PANTALLA PRINCIPAL
# ─────────────────────────────────────────────
if not st.session_state.ramo_sel or st.session_state.ramo_sel not in st.session_state.ramos:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("# Calculadora de Notas")
    st.markdown(
        "Selecciona o crea un ramo desde el panel izquierdo.\n\n"
        "Cada ramo puede tener múltiples grupos con reglas especiales: "
        "mínimos independientes, notas reprobatorias, tomar solo las N mejores, "
        "o usar la fórmula AVG-N a nivel de ramo (como Discretas)."
    )
    st.stop()

ramo_actual = st.session_state.ramo_sel
ramo_data   = st.session_state.ramos[ramo_actual]
grupos      = ramo_data["grupos"]
avg_n_ramo  = ramo_data.get("avg_n_ramo")

# Cabecera
col_h, col_tab = st.columns([3, 1])
with col_h:
    st.markdown(f"# {ramo_actual}")
with col_tab:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    label_btn = "📊 Ver notas" if st.session_state.modo == "estructura" else "⚙️ Estructura"
    if st.button(label_btn, use_container_width=True):
        st.session_state.modo = "estructura" if st.session_state.modo == "notas" else "notas"
        st.rerun()


# ════════════════════════════════════════════
#  MODO ESTRUCTURA
# ════════════════════════════════════════════
if st.session_state.modo == "estructura":
    st.markdown("### Configurar grupos de evaluación")
    st.caption(
        "Define los grupos, su peso en la nota final y las reglas especiales. "
        "Si el ramo usa AVG-N a nivel de ramo (ej: Discretas), actívalo abajo."
    )

    # ── Opción AVG-N a nivel de ramo ──
    with st.expander("🔢 Modo especial: AVG-N a nivel de ramo", expanded=avg_n_ramo is not None):
        st.markdown(
            "Activa esto si la nota final se calcula como **el promedio de las N mejores notas** "
            "entre todos los grupos (en vez de un promedio ponderado clásico).\n\n"
            "Ejemplo — Discretas: `NF = AVG3(I1, I2, (C1+C2)/2, E, E)` → 5 notas, se promedian las 3 mejores. "
            "El examen entra dos veces (marcar **'Cuenta doble'** en el grupo Examen)."
        )
        usar_avg_n = st.checkbox(
            "Usar AVG-N a nivel de ramo",
            value=avg_n_ramo is not None,
            key="chk_avg_n"
        )
        n_val = st.number_input(
            "N (cuántas mejores notas promediar):",
            min_value=1, max_value=20,
            value=int(avg_n_ramo) if avg_n_ramo else 3,
            key="num_avg_n",
            disabled=not usar_avg_n,
        )

    st.markdown("---")
    st.markdown("**Grupos de evaluación**")

    grupos_df = pd.DataFrame([{
        "Grupo":                   g["nombre"],
        "Ponderación (%)":         float(g["ponderacion"]),
        "Nota mínima indep.":      g.get("min_aprobacion") or None,
        "Reprobatorio":            bool(g.get("es_reprobatorio", False)),
        "N mejores (dentro grupo)": int(g["mejores_n"]) if g.get("mejores_n") else None,
        "Cuenta doble (AVG-N)":    bool(g.get("peso_doble", False)),
    } for g in grupos])

    edited = st.data_editor(
        grupos_df, num_rows="dynamic", use_container_width=True, key="editor_estructura",
        column_config={
            "Grupo": st.column_config.TextColumn(),
            "Ponderación (%)": st.column_config.NumberColumn(
                min_value=0, max_value=100, step=1,
                help="Solo relevante si NO usas AVG-N a nivel de ramo."
            ),
            "Nota mínima indep.": st.column_config.NumberColumn(
                min_value=1.0, max_value=7.0, format="%.1f", step=0.1,
                help="Nota mínima requerida en este grupo. Vacío = sin requisito."
            ),
            "Reprobatorio": st.column_config.CheckboxColumn(
                help="Si no se cumple la nota mínima, el ramo se reprueba independiente de la NF."
            ),
            "N mejores (dentro grupo)": st.column_config.NumberColumn(
                min_value=1, step=1,
                help="Dentro del grupo, contar solo las N mejores evaluaciones. Vacío = todas."
            ),
            "Cuenta doble (AVG-N)": st.column_config.CheckboxColumn(
                help="En AVG-N de ramo, este grupo entra dos veces en la lista (ej: examen en Discretas)."
            ),
        }
    )

    if not usar_avg_n:
        suma = edited["Ponderación (%)"].fillna(0).sum()
        if abs(suma - 100) > 0.5:
            st.warning(f"Las ponderaciones suman {suma:.0f}%. Deberían sumar 100%.")
        else:
            st.success("Las ponderaciones suman 100% ✓")

    if st.button("💾 Guardar estructura", type="primary"):
        nuevos = []
        for _, row in edited.iterrows():
            nombre_g = str(row["Grupo"]).strip() if pd.notna(row["Grupo"]) else ""
            if not nombre_g or nombre_g == "nan":
                continue
            pond   = float(row["Ponderación (%)"]) if pd.notna(row["Ponderación (%)"]) else 0.0
            min_ap = float(row["Nota mínima indep."]) if pd.notna(row["Nota mínima indep."]) else None
            repro  = bool(row["Reprobatorio"]) if pd.notna(row["Reprobatorio"]) else False
            mej_n  = int(row["N mejores (dentro grupo)"]) if pd.notna(row["N mejores (dentro grupo)"]) else None
            doble  = bool(row["Cuenta doble (AVG-N)"]) if pd.notna(row["Cuenta doble (AVG-N)"]) else False
            items_prev = next((g["items"] for g in grupos if g["nombre"] == nombre_g), [])
            nuevos.append({
                "nombre": nombre_g, "ponderacion": pond, "min_aprobacion": min_ap,
                "es_reprobatorio": repro, "mejores_n": mej_n, "peso_doble": doble,
                "items": items_prev,
            })

        st.session_state.ramos[ramo_actual]["grupos"]      = nuevos
        st.session_state.ramos[ramo_actual]["avg_n_ramo"]  = int(n_val) if usar_avg_n else None
        guardar_ramos(st.session_state.ramos)
        st.session_state.modo = "notas"
        st.toast("Estructura guardada.", icon="✅")
        st.rerun()

    st.divider()
    if st.button("🗑️ Eliminar este ramo"):
        del st.session_state.ramos[ramo_actual]
        guardar_ramos(st.session_state.ramos)
        st.session_state.ramo_sel = None
        st.rerun()


# ════════════════════════════════════════════
#  MODO NOTAS  (auto-guardado)
# ════════════════════════════════════════════
else:
    st.markdown(
        '<div style="margin-bottom:12px">'
        '<span class="autosave-chip">⟳ auto-guardado activado</span>'
        '</div>',
        unsafe_allow_html=True
    )

    # Mostrar fórmula si usa AVG-N
    if avg_n_ramo:
        grupos_nombres = []
        for g in grupos:
            doble = g.get("peso_doble", False)
            if doble:
                grupos_nombres.append(f"{g['nombre']} × 2")
            else:
                grupos_nombres.append(g["nombre"])
        formula_str = ", ".join(grupos_nombres)
        st.markdown(
            f'<div class="regla-box">'
            f'NF = AVG{avg_n_ramo}({formula_str})'
            f'</div>',
            unsafe_allow_html=True
        )

    grupos_actualizados = [dict(g) for g in grupos]
    hubo_cambio = False

    for idx, grupo in enumerate(grupos):
        nombre_g  = grupo["nombre"]
        pond_ramo = grupo.get("ponderacion", 0.0)
        min_ap    = grupo.get("min_aprobacion")
        es_repro  = grupo.get("es_reprobatorio", False)
        mejores_n = grupo.get("mejores_n")
        doble     = grupo.get("peso_doble", False)

        nota_g, peso_g = calcular_grupo(grupo)

        # Badge nota
        minimo_ref = min_ap if min_ap else 4.0
        if nota_g is not None:
            nota_badge = badge(f"{nota_g:.2f}", nota_color(nota_g, minimo_ref))
        else:
            nota_badge = badge("sin datos", "neutral")

        # Tags especiales
        tags = ""
        if mejores_n:
            tags += f'<span class="tag-special">⭐ {mejores_n} mejores</span>'
        if doble and avg_n_ramo:
            tags += f'<span class="tag-special">×2 en AVG{avg_n_ramo}</span>'
        if min_ap:
            tipo_min = "reprobatorio" if es_repro else "mínimo"
            tags += f'<span class="tag-special">⚠ {tipo_min} ≥{min_ap:.1f}</span>'

        # Mostrar ponderación solo si no usa avg_n_ramo
        pond_label = "" if avg_n_ramo else f" <span style='color:#7c7ca8;font-size:0.8rem'>· pondera {pond_ramo:.0f}%</span>"

        st.markdown(
            f"<div style='margin-bottom:4px'>"
            f"<span style='font-weight:600;font-size:1rem;color:#e2e2e8'>{nombre_g}</span> "
            f"{nota_badge}{pond_label}{tags}"
            f"</div>",
            unsafe_allow_html=True
        )

        items = grupo.get("items", [])
        df = pd.DataFrame(items)
        if df.empty:
            df = pd.DataFrame(columns=["Evaluación", "Nota", "Ponderación %"])

        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True,
            key=f"ed_{idx}",
            column_config={
                "Nota": st.column_config.NumberColumn(
                    min_value=1.0, max_value=7.0, format="%.1f", step=0.1),
                "Ponderación %": st.column_config.NumberColumn(
                    min_value=0, max_value=100, step=1,
                    help="Ponderación dentro de este grupo (debe sumar 100%)."
                ),
            }
        )

        nueva_lista = edited.dropna(how="all").to_dict("records")
        if nueva_lista != grupo.get("items", []):
            grupos_actualizados[idx] = {**grupo, "items": nueva_lista}
            hubo_cambio = True

        # Métricas del grupo
        if not edited.empty:
            try:
                grupo_tmp = {**grupo, "items": nueva_lista}
                nota_calc, peso_calc = calcular_grupo(grupo_tmp)

                if nota_calc is not None:
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric(f"Nota {nombre_g}", f"{nota_calc:.2f}")

                    if mejores_n:
                        n_ing = sum(1 for it in nueva_lista if it.get("Nota") not in [None, ""])
                        mc2.metric("Evaluaciones", f"{n_ing} ingresadas")
                    else:
                        mc2.metric("Avance en grupo", f"{peso_calc:.0f}%")

                    if min_ap:
                        if nota_calc >= min_ap:
                            mc3.metric("Requisito", f"✓ Cumple ≥{min_ap:.1f}")
                        else:
                            mc3.metric("Requisito", f"✗ No cumple ≥{min_ap:.1f}")

                    # Proyección dentro del grupo (solo si avance parcial y sin mejores_n)
                    if not mejores_n and 0 < peso_calc < 100:
                        falt = 100 - peso_calc
                        nec  = (4.0 - nota_calc) / (falt / 100)
                        if min_ap:
                            nec = max(nec, (min_ap - nota_calc) / (falt / 100))
                        if nec <= 1.0:
                            st.caption(f"El avance en **{nombre_g}** ya asegura el mínimo.")
                        elif nec > 7.0:
                            st.caption(f"No es posible alcanzar el mínimo en **{nombre_g}** con el {falt:.0f}% restante.")
                        else:
                            st.caption(f"Para el mínimo en **{nombre_g}**: necesitas **{nec:.2f}** en el {falt:.0f}% restante.")
            except Exception:
                pass

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Auto-guardar
    if hubo_cambio:
        st.session_state.ramos[ramo_actual]["grupos"] = grupos_actualizados
        guardar_ramos(st.session_state.ramos)

    # ── Resumen final ──────────────────────────────────
    st.divider()
    resultado = calcular_ramo(ramo_data)
    nf  = resultado["nota_final"]
    pc  = resultado["peso_completado"]
    aok = resultado["aprobacion_ok"]

    st.markdown("### Resumen del Ramo")
    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Final Actual", f"{nf:.2f}" if pc > 0 else "—")
    c2.metric("Avance Total", f"{pc:.0f}%")

    # Alertas reprobatorias
    fallidos = [g for g in resultado["grupos"] if not g["cumple"] and g["es_repro"]]
    if fallidos:
        nombres = ", ".join(f"**{g['nombre']}**" for g in fallidos)
        st.error(f"Requisito reprobatorio no cumplido en: {nombres}.")

    # Proyección global
    if pc > 0 and pc < 100:
        if avg_n_ramo:
            # Con AVG-N no es trivial calcular "cuánto necesito", mostrar nota actual
            c3.metric("Evaluaciones completadas", f"{pc:.0f}%")
            st.info(
                f"Con AVG{avg_n_ramo}: se promediarán las {avg_n_ramo} mejores notas de los grupos. "
                f"Nota actual si se tomaran las mejores ya ingresadas: **{nf:.2f}**."
            )
        else:
            falt = 100 - pc
            nec  = (4.0 - nf) / (falt / 100)
            if nec <= 1.0:
                c3.metric("Necesario para el 4.0", "Asegurado")
                st.success("El avance actual asegura la nota mínima de aprobación.")
            elif nec > 7.0:
                c3.metric("Necesario para el 4.0", f"{nec:.2f}")
                st.error(f"Con el {falt:.0f}% restante no es posible llegar al 4.0 (se necesitaría {nec:.2f}).")
            else:
                c3.metric("Necesario para el 4.0", f"{nec:.2f}")
                st.info(f"Necesitas promediar **{nec:.2f}** en el {falt:.0f}% de evaluaciones restantes.")
    elif pc >= 100:
        if nf >= 3.95 and aok:
            st.success(f"Nota final: **{nf:.2f}** — sobre el mínimo de aprobación.")
        elif nf >= 3.95 and not aok:
            st.warning(f"Nota final: **{nf:.2f}**, pero hay un requisito reprobatorio no cumplido.")
        else:
            st.error(f"Nota final: **{nf:.2f}** — bajo el mínimo de aprobación.")
