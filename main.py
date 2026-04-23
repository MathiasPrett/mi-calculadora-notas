import streamlit as st
import pandas as pd
import json
from streamlit_extras import local_storage_manager

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora de Notas", layout="wide", page_icon="🎓")

# ---------------------------------------------------------------------------
# LOCAL STORAGE
# ---------------------------------------------------------------------------
manager = local_storage_manager.LocalStorageManager(key="calculadora_notas_v2")

if not manager.ready():
    st.write("Cargando datos...")
    st.stop()

# ---------------------------------------------------------------------------
# MODELO DE DATOS
# ---------------------------------------------------------------------------
# Un ramo tiene:
#   { "grupos": [ { "nombre": str, "ponderacion": float, "min_aprobacion": float|None,
#                   "items": [ { "Evaluación": str, "Nota": float|None, "Ponderación %": float } ] } ] }
#
# Ramos simples (lista plana) se migran automáticamente al cargar.
# ---------------------------------------------------------------------------

def migrar_ramo_simple(data):
    """Si data es lista plana, lo convierte a estructura de grupos."""
    if isinstance(data, list):
        return {
            "grupos": [{
                "nombre": "General",
                "ponderacion": 100.0,
                "min_aprobacion": None,
                "items": data,
            }]
        }
    return data


def cargar_ramos():
    raw = manager.get("ramos_v2", None)
    # Intentar leer datos del formato antiguo (key "ramos")
    if raw is None:
        raw_old = manager.get("ramos", None)
        if raw_old:
            if isinstance(raw_old, str):
                try:
                    raw_old = json.loads(raw_old)
                except Exception:
                    raw_old = {}
            migrado = {}
            for nombre, data in raw_old.items():
                migrado[nombre] = migrar_ramo_simple(data)
            return migrado
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return {}
    for nombre in raw:
        raw[nombre] = migrar_ramo_simple(raw[nombre])
    return raw


def guardar_ramos(ramos):
    manager.set("ramos_v2", ramos)


def nuevo_ramo_vacio():
    return {
        "grupos": [{
            "nombre": "General",
            "ponderacion": 100.0,
            "min_aprobacion": None,
            "items": [],
        }]
    }


# ---------------------------------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------------------------------

def calcular_grupo(grupo):
    """Devuelve (nota_actual, peso_completado) con los ítems con datos completos."""
    items = grupo.get("items", [])
    notas, pesos = [], []
    for it in items:
        try:
            n = float(it.get("Nota"))
            p = float(it.get("Ponderación %"))
            notas.append(n)
            pesos.append(p)
        except (TypeError, ValueError):
            pass
    if not notas:
        return None, 0.0
    nota_actual = sum(n * (p / 100) for n, p in zip(notas, pesos))
    peso_total = sum(pesos)
    return nota_actual, peso_total


def calcular_ramo(ramo_data):
    """Devuelve resultados globales y por grupo."""
    grupos = ramo_data.get("grupos", [])
    resultados_grupos = []
    nota_final = 0.0
    peso_total_ramo = 0.0
    aprobacion_ok = True

    for g in grupos:
        nota_g, peso_g = calcular_grupo(g)
        pond_ramo = g.get("ponderacion", 0.0)
        min_ap = g.get("min_aprobacion")

        cumple_min = True
        if min_ap is not None and nota_g is not None:
            cumple_min = nota_g >= min_ap
        if not cumple_min:
            aprobacion_ok = False

        contrib = 0.0
        if nota_g is not None:
            contrib = nota_g * (pond_ramo / 100)
            peso_total_ramo += pond_ramo

        resultados_grupos.append({
            "nombre": g["nombre"],
            "nota": nota_g,
            "peso_completado": peso_g,
            "ponderacion_ramo": pond_ramo,
            "min_aprobacion": min_ap,
            "cumple_min": cumple_min,
            "contrib": contrib,
        })
        nota_final += contrib

    return {
        "nota_final": nota_final,
        "peso_ramo_completado": peso_total_ramo,
        "aprobacion_ok": aprobacion_ok,
        "grupos": resultados_grupos,
    }


# ---------------------------------------------------------------------------
# ESTADO DE SESIÓN
# ---------------------------------------------------------------------------
if "ramos" not in st.session_state:
    st.session_state.ramos = cargar_ramos()

if "ramo_sel" not in st.session_state:
    st.session_state.ramo_sel = None

if "editando_estructura" not in st.session_state:
    st.session_state.editando_estructura = False


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📚 Mis Ramos")
    st.divider()

    with st.expander("➕ Añadir Nuevo Ramo"):
        nuevo = st.text_input("Nombre del ramo:", key="input_nuevo_ramo").strip()
        if st.button("Crear"):
            if nuevo and nuevo not in st.session_state.ramos:
                st.session_state.ramos[nuevo] = nuevo_ramo_vacio()
                st.session_state.ramo_sel = nuevo
                st.session_state.editando_estructura = False
                guardar_ramos(st.session_state.ramos)
                st.rerun()
            elif nuevo in st.session_state.ramos:
                st.warning("Ya existe un ramo con ese nombre.")

    st.write("### Selecciona un Ramo:")
    for r in list(st.session_state.ramos.keys()):
        if st.button(f"📘 {r}", key=f"btn_{r}", use_container_width=True):
            st.session_state.ramo_sel = r
            st.session_state.editando_estructura = False
            st.rerun()


# ---------------------------------------------------------------------------
# CUERPO PRINCIPAL
# ---------------------------------------------------------------------------
if st.session_state.ramo_sel and st.session_state.ramo_sel in st.session_state.ramos:
    ramo_actual = st.session_state.ramo_sel
    ramo_data = st.session_state.ramos[ramo_actual]
    grupos = ramo_data["grupos"]

    # Cabecera
    col_title, col_actions = st.columns([3, 1])
    with col_title:
        st.title(f"📖 {ramo_actual}")
    with col_actions:
        st.write("")
        toggle_label = "✏️ Editar estructura" if not st.session_state.editando_estructura else "📊 Ver notas"
        if st.button(toggle_label, use_container_width=True):
            st.session_state.editando_estructura = not st.session_state.editando_estructura
            st.rerun()

    # =======================================================================
    # MODO: EDITAR ESTRUCTURA DE GRUPOS
    # =======================================================================
    if st.session_state.editando_estructura:
        st.subheader("Estructura del Ramo")
        st.caption(
            "Define los grupos de evaluación, su ponderación en la nota final "
            "y si cada grupo tiene nota mínima de aprobación independiente."
        )

        grupos_df = pd.DataFrame([
            {
                "Grupo": g["nombre"],
                "Ponderación en nota final (%)": float(g["ponderacion"]),
                "Nota mínima independiente": g.get("min_aprobacion") if g.get("min_aprobacion") else None,
            }
            for g in grupos
        ])

        edited_grupos = st.data_editor(
            grupos_df,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_grupos",
            column_config={
                "Grupo": st.column_config.TextColumn(),
                "Ponderación en nota final (%)": st.column_config.NumberColumn(
                    min_value=0, max_value=100, step=1
                ),
                "Nota mínima independiente": st.column_config.NumberColumn(
                    min_value=1.0, max_value=7.0, format="%.1f", step=0.1,
                    help="Nota mínima que debe obtenerse en este grupo para aprobar el ramo. "
                         "Dejar vacío si no aplica."
                ),
            }
        )

        suma_pond = edited_grupos["Ponderación en nota final (%)"].fillna(0).sum()
        if abs(suma_pond - 100) > 0.5:
            st.warning(f"Las ponderaciones suman {suma_pond:.0f}%. Deberían sumar 100%.")
        else:
            st.success("Las ponderaciones suman 100%. ✓")

        if st.button("💾 Guardar estructura", type="primary"):
            nuevos_grupos = []
            for _, row in edited_grupos.iterrows():
                nombre_g = str(row["Grupo"]).strip() if pd.notna(row["Grupo"]) else ""
                if not nombre_g or nombre_g == "nan":
                    continue
                pond_g = float(row["Ponderación en nota final (%)"]) if pd.notna(row["Ponderación en nota final (%)"]) else 0.0
                min_ap_raw = row["Nota mínima independiente"]
                min_ap = float(min_ap_raw) if pd.notna(min_ap_raw) else None

                # Preservar ítems existentes del grupo si el nombre coincide
                items_existentes = []
                for g_viejo in grupos:
                    if g_viejo["nombre"] == nombre_g:
                        items_existentes = g_viejo.get("items", [])
                        break

                nuevos_grupos.append({
                    "nombre": nombre_g,
                    "ponderacion": pond_g,
                    "min_aprobacion": min_ap,
                    "items": items_existentes,
                })

            st.session_state.ramos[ramo_actual]["grupos"] = nuevos_grupos
            guardar_ramos(st.session_state.ramos)
            st.session_state.editando_estructura = False
            st.toast("Estructura guardada.", icon="✅")
            st.rerun()

    # =======================================================================
    # MODO: INGRESAR NOTAS
    # =======================================================================
    else:
        grupos_actualizados = [dict(g) for g in grupos]

        for idx, grupo in enumerate(grupos):
            nombre_g = grupo["nombre"]
            pond_ramo = grupo.get("ponderacion", 0.0)
            min_ap = grupo.get("min_aprobacion")

            nota_g, peso_g = calcular_grupo(grupo)

            # Estado visual del grupo
            if nota_g is None:
                nota_str = "—"
            else:
                nota_str = f"{nota_g:.2f}"

            min_label = f" · mín. independiente **{min_ap:.1f}**" if min_ap else ""
            avance_label = f" · {peso_g:.0f}% completado" if nota_g is not None else ""

            with st.expander(
                f"**{nombre_g}** — Nota: {nota_str}{avance_label} | Pondera **{pond_ramo:.0f}%** en nota final{min_label}",
                expanded=True,
            ):
                items = grupo.get("items", [])
                df_items = pd.DataFrame(items)
                if df_items.empty:
                    df_items = pd.DataFrame(columns=["Evaluación", "Nota", "Ponderación %"])

                edited_items = st.data_editor(
                    df_items,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"editor_grupo_{idx}",
                    column_config={
                        "Nota": st.column_config.NumberColumn(
                            min_value=1.0, max_value=7.0, format="%.1f", step=0.1
                        ),
                        "Ponderación %": st.column_config.NumberColumn(
                            min_value=0, max_value=100, step=1
                        ),
                    },
                )

                # Métricas y proyección del grupo
                if not edited_items.empty:
                    try:
                        notas_tmp = pd.to_numeric(edited_items.get("Nota"), errors="coerce")
                        pesos_tmp = pd.to_numeric(edited_items.get("Ponderación %"), errors="coerce")
                        mask = notas_tmp.notna() & pesos_tmp.notna()

                        if mask.sum() > 0:
                            nt = notas_tmp[mask]
                            pt = pesos_tmp[mask]
                            nota_calc = (nt * (pt / 100)).sum()
                            peso_calc = pt.sum()

                            mc1, mc2, mc3 = st.columns(3)
                            mc1.metric(f"Nota {nombre_g}", f"{nota_calc:.2f}")
                            mc2.metric("Avance en grupo", f"{peso_calc:.0f}%")

                            if min_ap:
                                if nota_calc >= min_ap:
                                    mc3.metric("Requisito mínimo", f"✓ Cumple (≥{min_ap:.1f})")
                                else:
                                    mc3.metric("Requisito mínimo", f"✗ No cumple (≥{min_ap:.1f})")

                            # Proyección dentro del grupo
                            if peso_calc < 100:
                                faltante_g = 100 - peso_calc
                                # Nota necesaria para llegar al 4.0 en el grupo
                                nec_40 = (4.0 - nota_calc) / (faltante_g / 100)
                                # Si hay mínimo independiente, tomar el mayor requisito
                                nec_g = nec_40
                                if min_ap:
                                    nec_min = (min_ap - nota_calc) / (faltante_g / 100)
                                    nec_g = max(nec_40, nec_min)

                                if nec_g <= 1.0:
                                    st.caption(f"El avance en **{nombre_g}** ya asegura el mínimo del grupo.")
                                elif nec_g > 7.0:
                                    st.caption(
                                        f"Con el {faltante_g:.0f}% restante no es posible alcanzar "
                                        f"el mínimo en **{nombre_g}** (se necesitaría {nec_g:.2f})."
                                    )
                                else:
                                    st.caption(
                                        f"Para el mínimo en **{nombre_g}**, necesitas promediar "
                                        f"**{nec_g:.2f}** en el {faltante_g:.0f}% restante del grupo."
                                    )
                    except Exception:
                        pass

                # Botón guardar grupo
                if st.button(f"💾 Guardar {nombre_g}", key=f"save_grupo_{idx}"):
                    lista = edited_items.dropna(how="all").to_dict("records")
                    grupos_actualizados[idx] = {**grupo, "items": lista}
                    st.session_state.ramos[ramo_actual]["grupos"] = grupos_actualizados
                    guardar_ramos(st.session_state.ramos)
                    st.toast(f"{nombre_g} guardado.", icon="✅")
                    st.rerun()

        # -------------------------------------------------------------------
        # RESUMEN FINAL DEL RAMO
        # -------------------------------------------------------------------
        st.divider()
        resultado = calcular_ramo(ramo_data)
        nota_final = resultado["nota_final"]
        peso_completado = resultado["peso_ramo_completado"]
        aprobacion_ok = resultado["aprobacion_ok"]

        st.subheader("Resumen del Ramo")
        r1, r2, r3 = st.columns(3)
        r1.metric("Nota Final Actual", f"{nota_final:.2f}" if peso_completado > 0 else "—")
        r2.metric("Avance Total", f"{peso_completado:.0f}%")

        # Alertas por requisitos independientes no cumplidos
        grupos_fallidos = [g for g in resultado["grupos"] if not g["cumple_min"] and g["min_aprobacion"]]
        if grupos_fallidos:
            nombres_fallidos = ", ".join(f"**{g['nombre']}**" for g in grupos_fallidos)
            st.error(
                f"Requisito mínimo independiente no cumplido en: {nombres_fallidos}. "
                "El ramo podría no aprobarse aunque la nota final sea ≥4.0."
            )

        # Proyección nota final
        if peso_completado > 0 and peso_completado < 100:
            faltante_ramo = 100 - peso_completado
            nec_final = (4.0 - nota_final) / (faltante_ramo / 100)
            if nec_final <= 1.0:
                r3.metric("Necesario para el 4.0", "Asegurado")
                st.success("El avance actual asegura la nota mínima de aprobación global.")
            elif nec_final > 7.0:
                r3.metric("Necesario para el 4.0", f"{nec_final:.2f}")
                st.error(
                    f"Con el {faltante_ramo:.0f}% restante no es posible llegar al 4.0 global "
                    f"(se necesitaría {nec_final:.2f})."
                )
            else:
                r3.metric("Necesario para el 4.0", f"{nec_final:.2f}")
                st.info(
                    f"Necesitas promediar **{nec_final:.2f}** en el {faltante_ramo:.0f}% "
                    "de evaluaciones restantes."
                )
        elif peso_completado == 100:
            if nota_final >= 3.95 and aprobacion_ok:
                st.success(f"Nota final: **{nota_final:.2f}** — sobre el mínimo de aprobación.")
            elif nota_final >= 3.95 and not aprobacion_ok:
                st.warning(
                    f"Nota final: **{nota_final:.2f}**, pero hay requisitos independientes no cumplidos."
                )
            else:
                st.error(f"Nota final: **{nota_final:.2f}** — bajo el mínimo de aprobación.")

        # Eliminar ramo
        st.divider()
        if st.button("🗑️ Eliminar este ramo"):
            del st.session_state.ramos[ramo_actual]
            guardar_ramos(st.session_state.ramos)
            st.session_state.ramo_sel = None
            st.rerun()

# ---------------------------------------------------------------------------
# PANTALLA DE BIENVENIDA
# ---------------------------------------------------------------------------
else:
    st.title("Calculadora de Notas 🎓")
    st.write("Selecciona o crea un ramo desde el panel izquierdo para comenzar.")
    st.info(
        "Para ramos simples, agrega evaluaciones directamente. "
        "Para ramos con requisitos independientes (ej: nota de tareas y nota de pruebas por separado), "
        "usa el botón **Editar estructura** dentro del ramo para configurar grupos con mínimos independientes."
    )
