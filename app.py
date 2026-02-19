import math
import streamlit as st
from datetime import datetime, date, time

import db
from pdf_export import build_pdf

st.set_page_config(
    page_title="Movimientos Almacén",
    layout="wide",
    initial_sidebar_state="collapsed"
)


db.init_db()

# ---------------------------
# Estado / navegación
# ---------------------------
if "screen" not in st.session_state:
    st.session_state.screen = "home"  # home | comment | manage | pdf

if "selected_type_id" not in st.session_state:
    st.session_state.selected_type_id = None

if "selected_type_name" not in st.session_state:
    st.session_state.selected_type_name = None


def go(screen: str):
    st.session_state.screen = screen
    st.rerun()


# ---------------------------
# Estilos móvil (compacto)
# ---------------------------
st.markdown("""
<style>
/* Quita límites de ancho internos (Streamlit) */
[data-testid="stAppViewContainer"]{
    padding: 0 !important;
}
[data-testid="stMainBlockContainer"]{
    max-width: 100% !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    padding-top: 0.4rem !important;
    padding-bottom: 4rem !important;
}

/* Botones compactos */
div.stButton > button {
    width: 100%;
    padding: 0.42rem 0.45rem !important;
    font-size: 0.78rem !important;
    border-radius: 12px !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Columnas: evita que se apilen */
div[data-testid="stHorizontalBlock"]{
    flex-wrap: nowrap !important;
    gap: 0.35rem !important;
}
div[data-testid="column"], div[data-testid="stColumn"]{
    padding: 0 !important;
    min-width: 0 !important;
    flex: 1 1 0px !important;
}

/* Reduce espacio vertical entre elementos */
h1, h2, h3 { margin-bottom: 0.35rem !important; }
hr { margin: 0.6rem 0 !important; }
</style>
""", unsafe_allow_html=True)



# ---------------------------
# Header
# ---------------------------
st.title("📦 Movimientos (pistola)")

# ---------------------------
# Barra navegación (arriba)
# ---------------------------
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("🏠 Movimientos"):
        go("home")
with nav2:
    if st.button("➕/🗑️ Botones"):
        go("manage")
with nav3:
    if st.button("📄 PDF"):
        go("pdf")

# ============================================================
# PANTALLA HOME: grid de botones + últimos movimientos
# ============================================================
if st.session_state.screen == "home":
    st.subheader("Toca un botón para registrar")

    types = db.list_movement_types()

    if not types:
        st.info("No tienes botones todavía. Ve a ➕/🗑️ Botones para crear el primero.")
    else:
        # Ajusta esto: 3 o 4 columnas según tu móvil
        cols_per_row = 4  # prueba 4 si quieres más juntos

        rows = math.ceil(len(types) / cols_per_row)
        idx = 0

        for _ in range(rows):
            cols = st.columns(cols_per_row)
            for c in range(cols_per_row):
                if idx < len(types):
                    t = types[idx]
                    with cols[c]:
                        if st.button(t["name"], key=f"movebtn_{t['id']}"):
                            st.session_state.selected_type_id = int(t["id"])
                            st.session_state.selected_type_name = t["name"]
                            go("comment")
                    idx += 1

    st.divider()
    st.subheader("Últimos movimientos")

    rows = db.list_movements(limit=20)
    if not rows:
        st.caption("Aún no has registrado movimientos.")
    else:
        for r in rows:
            comment = r["comment"] or ""
            st.write(f"**{r['hhmmss']}** — {r['movement_name']}  \n_{comment}_")


# ============================================================
# PANTALLA COMMENT: comentario + guardar
# ============================================================
elif st.session_state.screen == "comment":
    name = st.session_state.selected_type_name
    type_id = st.session_state.selected_type_id

    if not type_id or not name:
        st.warning("No hay movimiento seleccionado.")
        if st.button("Volver"):
            go("home")
    else:
        st.subheader(f"📝 Comentario para: {name}")
        st.caption("Se guardará con hora:minuto:segundo automáticamente.")

        comment = st.text_area(
            "Comentario (opcional)",
            height=120,
            placeholder="Ej: Ubicación A-12, caja dañada, etc.",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar", key="save_move"):
                db.add_movement(type_id, name, comment)
                st.success("Movimiento guardado ✅")

                st.session_state.selected_type_id = None
                st.session_state.selected_type_name = None
                go("home")

        with c2:
            if st.button("Cancelar"):
                st.session_state.selected_type_id = None
                st.session_state.selected_type_name = None
                go("home")


# ============================================================
# PANTALLA MANAGE: crear + borrar botones
# ============================================================
elif st.session_state.screen == "manage":
    st.subheader("➕ Crear botón de movimiento")

    new_name = st.text_input("Nombre del botón", placeholder="Ej: Picking / Ubicar palet / Entrada...")

    if st.button("Crear botón"):
        ok, err = db.add_movement_type(new_name)
        if ok:
            st.success("Botón creado ✅")
            st.rerun()
        else:
            st.error(err or "No se pudo crear")

    st.divider()
    st.subheader("🗑️ Eliminar botones")

    types = db.list_movement_types()
    if not types:
        st.caption("No hay botones para borrar.")
    else:
        options = {f"{t['name']} (id {t['id']})": int(t["id"]) for t in types}
        label = st.selectbox("Selecciona un botón", list(options.keys()))
        delete_id = options[label]

        if st.button("Eliminar seleccionado"):
            db.delete_movement_type(delete_id)
            st.success("Botón eliminado 🗑️")
            st.rerun()


# ============================================================
# PANTALLA PDF: exportar por día
# ============================================================
elif st.session_state.screen == "pdf":
    st.subheader("📄 Exportar a PDF")

    selected_day = st.date_input("Día a exportar", value=date.today())

    start_dt = datetime.combine(selected_day, time(0, 0, 0))
    end_dt = datetime.combine(selected_day, time(23, 59, 59))

    rows = db.list_movements_between(
        start_dt.isoformat(timespec="seconds"),
        end_dt.isoformat(timespec="seconds"),
    )

    st.caption(f"Movimientos encontrados: {len(rows)}")

    if rows:
        pdf_bytes = build_pdf(rows, title=f"Registro de movimientos - {selected_day.isoformat()}")

        st.download_button(
            label="⬇️ Descargar PDF",
            data=pdf_bytes,
            file_name=f"movimientos_{selected_day.isoformat()}.pdf",
            mime="application/pdf",
        )

        st.divider()
        st.subheader("Vista previa")
        for r in rows[:30]:
            st.write(f"**{r['hhmmss']}** — {r['movement_name']}  \n_{(r['comment'] or '')}_")
    else:
        st.info("No hay movimientos ese día.")

    if st.button("Volver"):
        go("home")
