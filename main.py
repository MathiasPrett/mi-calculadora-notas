import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
from streamlit_extras import local_storage_manager

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
st.set_page_config(page_title="Mis Notas", layout="wide", page_icon="🎓")

# ─────────────────────────────────────────────
#  LOCAL STORAGE
# ─────────────────────────────────────────────
manager = local_storage_manager.LocalStorageManager(key="calculadora_notas_v5")
if not manager.ready():
    st.info("⏳ Cargando datos...")
    st.stop()

# ─────────────────────────────────────────────
#  MODELO DE DATOS
# ─────────────────────────────────────────────
# Ítem:
#   Evaluación:   str
#   Nota:         float | None
#   Ponderación %: float
#   Fecha:        str "YYYY-MM-DD" | None
#   Contenidos:   str | None
#
# Grupo:
#   nombre:      str
#   ponderacion: float   (% sobre la nota final del ramo)
#   items:       list[Ítem]
#
# Ramo:
#   grupos: list[Grupo]

def migrar_ramo(data):
    """Convierte cualquier formato anterior al modelo actual."""
    if isinstance(data, list):
        items = [{**it, "Fecha": it.get("Fecha", None), "Contenidos": it.get("Contenidos", None)}
                 for it in data]
        return {"grupos": [{"nombre": "General", "ponderacion": 100.0, "items": items}]}
    grupos_nuevos = []
    for g in data.get("grupos", []):
        items = [{
            "Evaluación":   it.get("Evaluación", ""),
            "Nota":         it.get("Nota", None),
            "Ponderación %": it.get("Ponderación %", 0.0),
            "Fecha":        it.get("Fecha", None),
            "Contenidos":   it.get("Contenidos", None),
        } for it in g.get("items", [])]
        grupos_nuevos.append({
            "nombre":      g.get("nombre", "General"),
            "ponderacion": g.get("ponderacion", 100.0),
            "items":       items,
        })
    return {"grupos": grupos_nuevos}


def cargar_ramos():
    raw = manager.get("ramos_v5", None)
    if raw is None:
        for old_key in ["ramos_v4", "ramos_v3", "ramos_v2", "ramos"]:
            raw_old = manager.get(old_key, None)
            if raw_old:
                if isinstance(raw_old, str):
                    try:    raw_old = json.loads(raw_old)
                    except: raw_old = {}
                return {k: migrar_ramo(v) for k, v in raw_old.items()}
        return {}
    if isinstance(raw, str):
        try:    raw = json.loads(raw)
        except: return {}
    return {k: migrar_ramo(v) for k, v in raw.items()}


def guardar_ramos(ramos):
    manager.set("ramos_v5", ramos)


def ramo_nuevo():
    return {"grupos": [{"nombre": "General", "ponderacion": 100.0, "items": []}]}


# ─────────────────────────────────────────────
#  CÁLCULO
# ─────────────────────────────────────────────
def calcular_grupo(grupo):
    """Devuelve (nota_ponderada, peso_completado)."""
    validos = []
    for it in grupo.get("items", []):
        try:
            validos.append({"nota": float(it["Nota"]), "peso": float(it["Ponderación %"])})
        except (TypeError, ValueError, KeyError):
            pass
    if not validos:
        return None, 0.0
    nota = sum(v["nota"] * v["peso"] / 100 for v in validos)
    peso = sum(v["peso"] for v in validos)
    return nota, peso


def calcular_ramo(ramo_data):
    nota_final = 0.0
    peso_completado = 0.0
    detalle = []
    for g in ramo_data.get("grupos", []):
        nota_g, peso_g = calcular_grupo(g)
        pond = g.get("ponderacion", 0.0)
        contrib = nota_g * (pond / 100) if nota_g is not None else 0.0
        if nota_g is not None:
            peso_completado += pond
        nota_final += contrib
        detalle.append({"nombre": g["nombre"], "nota": nota_g,
                        "peso_g": peso_g, "ponderacion": pond})
    return {"nota_final": nota_final, "peso_completado": peso_completado, "grupos": detalle}


def proximas_evaluaciones(ramos, dias=14):
    hoy   = date.today()
    limite = hoy + timedelta(days=dias)
    result = []
    for nombre_ramo, ramo_data in ramos.items():
        for grupo in ramo_data.get("grupos", []):
            for it in grupo.get("items", []):
                fecha_str = it.get("Fecha")
                if not fecha_str:
                    continue
                try:
                    fecha = date.fromisoformat(str(fecha_str)[:10])
                    if hoy <= fecha <= limite:
                        result.append({
                            "ramo":       nombre_ramo,
                            "grupo":      grupo["nombre"],
                            "evaluacion": it.get("Evaluación", ""),
                            "fecha":      fecha,
                            "contenidos": it.get("Contenidos") or "",
                            "tiene_nota": it.get("Nota") not in [None, ""],
                        })
                except (ValueError, TypeError):
                    pass
    return sorted(result, key=lambda x: x["fecha"])


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def parse_date(v):
    if not v:
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except Exception:
        return None


def serializar_items(edited_df):
    """Convierte el DataFrame editado a lista de dicts guardable."""
    result = []
    for _, row in edited_df.iterrows():
        eval_v = row.get("Evaluación")
        nota_v = row.get("Nota")
        pond_v = row.get("Ponderación %")
        # Saltar filas completamente vacías
        if (pd.isna(eval_v) or str(eval_v).strip() == "") and pd.isna(nota_v):
            continue
        fecha_v = row.get("Fecha")
        if fecha_v is not None and not (isinstance(fecha_v, float) and pd.isna(fecha_v)):
            try:
                fecha_iso = pd.Timestamp(fecha_v).date().isoformat()
            except Exception:
                fecha_iso = None
        else:
            fecha_iso = None
        cont_v = row.get("Contenidos")
        result.append({
            "Evaluación":   str(eval_v).strip() if pd.notna(eval_v) else "",
            "Nota":         float(nota_v) if pd.notna(nota_v) else None,
            "Ponderación %": float(pond_v) if pd.notna(pond_v) else 0.0,
            "Fecha":        fecha_iso,
            "Contenidos":   str(cont_v) if pd.notna(cont_v) and str(cont_v).strip() else None,
        })
    return result


# ─────────────────────────────────────────────
#  ESTADO
# ─────────────────────────────────────────────
if "ramos" not in st.session_state:
    st.session_state.ramos = cargar_ramos()
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "modo_ramo" not in st.session_state:
    st.session_state.modo_ramo = "notas"


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 Mis Notas")
    st.divider()

    if st.button("🏠 Inicio", use_container_width=True,
                 type="primary" if st.session_state.pagina == "inicio" else "secondary"):
        st.session_state.pagina = "inicio"
        st.rerun()

    st.markdown("**Ramos**")
    for r in list(st.session_state.ramos.keys()):
        res = calcular_ramo(st.session_state.ramos[r])
        nota_str = f" · {res['nota_final']:.1f}" if res["peso_completado"] > 0 else ""
        es_activo = st.session_state.pagina == r
        if st.button(
            f"{'▶ ' if es_activo else ''}{r}{nota_str}",
            key=f"sb_{r}", use_container_width=True,
            type="primary" if es_activo else "secondary",
        ):
            st.session_state.pagina = r
            st.session_state.modo_ramo = "notas"
            st.rerun()

    st.divider()
    with st.expander("＋ Nuevo ramo"):
        nuevo = st.text_input("", key="input_nuevo",
                              placeholder="Ej: Cálculo II").strip()
        if st.button("Crear", key="btn_crear"):
            if nuevo and nuevo not in st.session_state.ramos:
                st.session_state.ramos[nuevo] = ramo_nuevo()
                st.session_state.pagina = nuevo
                st.session_state.modo_ramo = "notas"
                guardar_ramos(st.session_state.ramos)
                st.rerun()
            elif nuevo in st.session_state.ramos:
                st.warning("Ya existe un ramo con ese nombre.")


# ═════════════════════════════════════════════
#  PÁGINA: INICIO
# ═════════════════════════════════════════════
if st.session_state.pagina == "inicio":
    st.title("Resumen General")

    if not st.session_state.ramos:
        st.info("No tienes ramos aún. Crea uno desde el panel izquierdo.")
        st.stop()

    # Tarjetas de ramos
    st.subheader("Estado de ramos")
    cols = st.columns(min(len(st.session_state.ramos), 4))
    for i, (nombre_r, ramo_d) in enumerate(st.session_state.ramos.items()):
        res = calcular_ramo(ramo_d)
        nf = res["nota_final"]
        pc = res["peso_completado"]
        with cols[i % 4]:
            if pc == 0:
                delta = "Sin notas"
            elif pc >= 100:
                delta = "✓ Completado" if nf >= 3.95 else "✗ Reprobado"
            else:
                delta = f"{pc:.0f}% completado"
            st.metric(nombre_r, f"{nf:.2f}" if pc > 0 else "—", delta)
            if st.button("Ver ramo", key=f"dash_{nombre_r}", use_container_width=True):
                st.session_state.pagina = nombre_r
                st.session_state.modo_ramo = "notas"
                st.rerun()

    st.divider()

    # Próximas evaluaciones
    proximas = proximas_evaluaciones(st.session_state.ramos, dias=14)
    st.subheader("📅 Próximas 2 semanas")

    if not proximas:
        st.info("No hay evaluaciones con fecha registrada en las próximas dos semanas.")
    else:
        hoy = date.today()

        # Mini calendario: días únicos como columnas
        dias_unicos = sorted(set(p["fecha"] for p in proximas))
        cal_cols = st.columns(min(len(dias_unicos), 7))
        for ci, dia in enumerate(dias_unicos[:7]):
            delta_d = (dia - hoy).days
            if delta_d == 0:    etiqueta = "**Hoy**"
            elif delta_d == 1:  etiqueta = "**Mañana**"
            else:               etiqueta = f"**{dia.strftime('%a %d/%m')}**"
            evals_dia = [p for p in proximas if p["fecha"] == dia]
            with cal_cols[ci]:
                st.markdown(etiqueta)
                for ev in evals_dia:
                    st.caption(f"🔔 {ev['ramo']}\n{ev['evaluacion']}")

        st.divider()

        # Tablón detallado
        st.subheader("📋 Detalle de evaluaciones")
        for p in proximas:
            delta_d = (p["fecha"] - hoy).days
            if delta_d == 0:    cuando = "Hoy"
            elif delta_d == 1:  cuando = "Mañana"
            else:               cuando = f"En {delta_d} días"
            fecha_str = p["fecha"].strftime("%d/%m/%Y")

            with st.expander(
                f"{p['evaluacion']}  ·  {p['ramo']}  ·  {fecha_str}  ·  {cuando}",
                expanded=delta_d <= 1,
            ):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.markdown(f"**Ramo:** {p['ramo']}")
                    st.markdown(f"**Grupo:** {p['grupo']}")
                    st.markdown(f"**Fecha:** {fecha_str}")
                    if p["tiene_nota"]:
                        st.success("Ya tiene nota registrada")
                with col_b:
                    if p["contenidos"]:
                        st.markdown("**Contenidos:**")
                        st.markdown(p["contenidos"])
                    else:
                        st.caption("Sin contenidos registrados.")

    st.stop()


# ═════════════════════════════════════════════
#  PÁGINA: RAMO
# ═════════════════════════════════════════════
ramo_actual = st.session_state.pagina
if ramo_actual not in st.session_state.ramos:
    st.session_state.pagina = "inicio"
    st.rerun()

ramo_data = st.session_state.ramos[ramo_actual]
grupos    = ramo_data["grupos"]

# Cabecera
col_h, col_btn = st.columns([3, 1])
with col_h:
    st.title(ramo_actual)
with col_btn:
    st.write("")
    label_btn = "📊 Ver notas" if st.session_state.modo_ramo == "estructura" else "⚙️ Grupos"
    if st.button(label_btn, use_container_width=True):
        st.session_state.modo_ramo = (
            "estructura" if st.session_state.modo_ramo == "notas" else "notas"
        )
        st.rerun()


# ═════════════════════════════════════════════
#  MODO ESTRUCTURA (solo grupos básicos)
# ═════════════════════════════════════════════
if st.session_state.modo_ramo == "estructura":
    st.subheader("Grupos de evaluación")
    st.caption(
        "Define los grupos del ramo y cuánto pondera cada uno en la nota final. "
        "Las ponderaciones deben sumar 100%."
    )

    grupos_df = pd.DataFrame([{
        "Grupo":           g["nombre"],
        "Ponderación (%)": float(g["ponderacion"]),
    } for g in grupos])

    edited_grupos = st.data_editor(
        grupos_df, num_rows="dynamic", use_container_width=True,
        key="editor_grupos",
        column_config={
            "Grupo": st.column_config.TextColumn(),
            "Ponderación (%)": st.column_config.NumberColumn(
                min_value=0, max_value=100, step=1
            ),
        }
    )

    suma = edited_grupos["Ponderación (%)"].fillna(0).sum()
    if abs(suma - 100) > 0.5:
        st.warning(f"Las ponderaciones suman {suma:.0f}%. Deberían sumar 100%.")
    else:
        st.success("Las ponderaciones suman 100% ✓")

    if st.button("💾 Guardar grupos", type="primary"):
        nuevos = []
        for _, row in edited_grupos.iterrows():
            nombre_g = str(row["Grupo"]).strip() if pd.notna(row["Grupo"]) else ""
            if not nombre_g or nombre_g == "nan":
                continue
            pond = float(row["Ponderación (%)"]) if pd.notna(row["Ponderación (%)"]) else 0.0
            items_prev = next((g["items"] for g in grupos if g["nombre"] == nombre_g), [])
            nuevos.append({"nombre": nombre_g, "ponderacion": pond, "items": items_prev})

        st.session_state.ramos[ramo_actual]["grupos"] = nuevos
        guardar_ramos(st.session_state.ramos)
        st.session_state.modo_ramo = "notas"
        st.success("Grupos guardados.")
        st.rerun()

    st.divider()
    if st.button("🗑️ Eliminar este ramo"):
        del st.session_state.ramos[ramo_actual]
        guardar_ramos(st.session_state.ramos)
        st.session_state.pagina = "inicio"
        st.rerun()


# ═════════════════════════════════════════════
#  MODO NOTAS
# ═════════════════════════════════════════════
else:
    for idx, grupo in enumerate(grupos):
        nombre_g  = grupo["nombre"]
        pond_ramo = grupo.get("ponderacion", 0.0)
        nota_g, peso_g = calcular_grupo(grupo)

        if nota_g is not None:
            nota_label = f"Nota: {nota_g:.2f} · {peso_g:.0f}% completado"
        else:
            nota_label = "Sin notas aún"
        pond_label = f" · pondera {pond_ramo:.0f}%" if len(grupos) > 1 else ""

        with st.expander(f"**{nombre_g}** — {nota_label}{pond_label}", expanded=True):

            # Preparar DataFrame
            items = grupo.get("items", [])
            df_base = pd.DataFrame(items) if items else pd.DataFrame(
                columns=["Evaluación", "Nota", "Ponderación %", "Fecha", "Contenidos"]
            )
            for col in ["Evaluación", "Nota", "Ponderación %", "Fecha", "Contenidos"]:
                if col not in df_base.columns:
                    df_base[col] = None

            df_base["Fecha"] = df_base["Fecha"].apply(parse_date)

            edited = st.data_editor(
                df_base[["Evaluación", "Nota", "Ponderación %", "Fecha", "Contenidos"]],
                num_rows="dynamic",
                use_container_width=True,
                key=f"ed_{ramo_actual}_{idx}",
                column_config={
                    "Evaluación": st.column_config.TextColumn(),
                    "Nota": st.column_config.NumberColumn(
                        min_value=1.0, max_value=7.0, format="%.1f", step=0.1
                    ),
                    "Ponderación %": st.column_config.NumberColumn(
                        min_value=0, max_value=100, step=1,
                        help="Peso de esta evaluación dentro del grupo."
                    ),
                    "Fecha": st.column_config.DateColumn(
                        label="Fecha",
                        format="DD/MM/YYYY",
                        help="Fecha de la evaluación (opcional).",
                    ),
                    "Contenidos": st.column_config.TextColumn(
                        label="Contenidos",
                        help="Materia o contenidos de la evaluación (opcional).",
                        width="large",
                    ),
                },
            )

            # Métricas en tiempo real (calculadas del editor, sin guardar)
            try:
                nt = pd.to_numeric(edited["Nota"],          errors="coerce")
                pt = pd.to_numeric(edited["Ponderación %"], errors="coerce")
                mask = nt.notna() & pt.notna()
                if mask.sum() > 0:
                    nota_calc = (nt[mask] * pt[mask] / 100).sum()
                    peso_calc = pt[mask].sum()
                    mc1, mc2 = st.columns(2)
                    mc1.metric(f"Nota {nombre_g}", f"{nota_calc:.2f}")
                    mc2.metric("Avance en grupo", f"{peso_calc:.0f}%")
                    if 0 < peso_calc < 100:
                        falt = 100 - peso_calc
                        nec  = (4.0 - nota_calc) / (falt / 100)
                        if nec <= 1.0:
                            st.caption("El avance actual ya asegura el mínimo en este grupo.")
                        elif nec > 7.0:
                            st.caption(f"No es posible alcanzar el 4.0 en {nombre_g} con el {falt:.0f}% restante.")
                        else:
                            st.caption(f"Para el 4.0 en {nombre_g}: necesitas **{nec:.2f}** en el {falt:.0f}% restante.")
            except Exception:
                pass

            # Guardar
            if st.button(f"💾 Guardar {nombre_g}", key=f"save_{ramo_actual}_{idx}"):
                nueva_lista = serializar_items(edited)
                st.session_state.ramos[ramo_actual]["grupos"][idx]["items"] = nueva_lista
                guardar_ramos(st.session_state.ramos)
                st.success(f"{nombre_g} guardado.")
                st.rerun()

    # Resumen final
    st.divider()
    res = calcular_ramo(ramo_data)
    nf  = res["nota_final"]
    pc  = res["peso_completado"]

    st.subheader("Resumen del Ramo")
    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Final Actual", f"{nf:.2f}" if pc > 0 else "—")
    c2.metric("Avance Total",      f"{pc:.0f}%")

    if 0 < pc < 100:
        falt = 100 - pc
        nec  = (4.0 - nf) / (falt / 100)
        if nec <= 1.0:
            c3.metric("Necesario para el 4.0", "Asegurado")
            st.success("El avance actual asegura la nota mínima de aprobación.")
        elif nec > 7.0:
            c3.metric("Necesario para el 4.0", f"{nec:.2f}")
            st.error(f"Con el {falt:.0f}% restante no es posible llegar al 4.0 (necesitarías {nec:.2f}).")
        else:
            c3.metric("Necesario para el 4.0", f"{nec:.2f}")
            st.info(f"Necesitas promediar **{nec:.2f}** en el {falt:.0f}% de evaluaciones restantes.")
    elif pc >= 100:
        if nf >= 3.95:
            st.success(f"Nota final: **{nf:.2f}** — sobre el mínimo de aprobación.")
        else:
            st.error(f"Nota final: **{nf:.2f}** — bajo el mínimo de aprobación.")