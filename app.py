import math
import streamlit as st
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

import db
from pdf_export import build_pdf

MADRID = ZoneInfo("Europe/Madrid")

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
    st.session_state.screen = "home"  # home | comment | manage | pdf | edit

if "selected_type_id" not in st.session_state:
    st.session_state.selected_type_id = None
if "selected_type_name" not in st.session_state:
    st.session_state.selected_type_name = None

# Dist. car. selections
if "dist_car_carro" not in st.session_state:
    st.session_state.dist_car_carro = None
if "dist_car_zona" not in st.session_state:
    st.session_state.dist_car_zona = None

# Edit movement
if "edit_movement_id" not in st.session_state:
    st.session_state.edit_movement_id = None


def go(screen: str):
    st.session_state.screen = screen
    st.rerun()


def is_dist_car(name: str) -> bool:
    return (name or "").strip().lower() == "dist. car.".lower()


# ---------------------------
# CSS móvil (ancho + compacto)
# ---------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{ padding: 0 !important; }
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

h1, h2, h3 { margin-bottom: 0.35rem !important; }
hr { margin: 0.6rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Header + nav
# ---------------------------
st.title("📦 Movimientos (pistola)")

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
# HOME
# ============================================================
if st.session_state.screen == "home":
    st.subheader("Toca un botón para registrar")

    types = db.list_movement_types()

    if not types:
        st.info("No tienes botones todavía. Ve a ➕/🗑️ Botones para crear el primero.")
    else:
        cols_per_row = 4
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

                            st.session_state.dist_car_carro = None
                            st.session_state.dist_car_zona = None

                            go("comment")
                    idx += 1

    st.divider()

    # Historial (editar / eliminar)
    with st.expander("📜 Historial (editar / eliminar)", expanded=False):
        rows = db.list_movements(limit=60)
        if not rows:
            st.caption("Aún no has registrado movimientos.")
        else:
            for r in rows:
                comment = r["comment"] or ""
                st.write(f"**{r['hhmmss']}** — {r['movement_name']}  \n_{comment}_")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ Editar", key=f"edit_{r['id']}"):
                        st.session_state.edit_movement_id = int(r["id"])
                        go("edit")
                with c2:
                    if st.button("🗑️ Eliminar", key=f"del_{r['id']}"):
                        db.delete_movement(int(r["id"]))
                        st.success("Movimiento eliminado.")
                        st.rerun()

                st.markdown("---")


# ============================================================
# COMMENT
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

        # --- Especial Dist. car. ---
        if is_dist_car(name):
            st.caption("Selecciona Carro y Zona (opcional).")

            st.markdown("**Carro (1–26)**")
            carros = list(range(1, 27))
            carros_cols = 6
            rows_c = math.ceil(len(carros) / carros_cols)
            idx = 0
            for _ in range(rows_c):
                cols = st.columns(carros_cols)
                for c in range(carros_cols):
                    if idx < len(carros):
                        n = carros[idx]
                        with cols[c]:
                            if st.button(str(n), key=f"carro_{n}"):
                                st.session_state.dist_car_carro = n
                                st.rerun()
                        idx += 1

            st.markdown("**Zona (1–11)**")
            zonas = list(range(1, 12))
            zonas_cols = 6
            rows_z = math.ceil(len(zonas) / zonas_cols)
            idx = 0
            for _ in range(rows_z):
                cols = st.columns(zonas_cols)
                for c in range(zonas_cols):
                    if idx < len(zonas):
                        z = zonas[idx]
                        with cols[c]:
                            if st.button(str(z), key=f"zona_{z}"):
                                st.session_state.dist_car_zona = z
                                st.rerun()
                        idx += 1

            carro = st.session_state.dist_car_carro
            zona = st.session_state.dist_car_zona
            st.info(f"Seleccionado → Carro: {carro if carro else '-'} | Zona: {zona if zona else '-'}")

        st.caption("Se guardará con hora:minuto:segundo automáticamente (Europe/Madrid).")

        comment = st.text_area(
            "Comentario (opcional)",
            height=120,
            placeholder="Ej: Ubicación A-12, caja dañada, etc.",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar", key="save_move"):
                final_comment = (comment or "").strip()

                if is_dist_car(name):
                    carro = st.session_state.dist_car_carro
                    zona = st.session_state.dist_car_zona
                    prefix_parts = []
                    if carro:
                        prefix_parts.append(f"Carro:{carro}")
                    if zona:
                        prefix_parts.append(f"Zona:{zona}")
                    if prefix_parts:
                        prefix = " ".join(prefix_parts)
                        final_comment = f"{prefix} - {final_comment}" if final_comment else prefix

                db.add_movement(type_id, name, final_comment)

                st.success("Movimiento guardado ✅")

                st.session_state.selected_type_id = None
                st.session_state.selected_type_name = None
                st.session_state.dist_car_carro = None
                st.session_state.dist_car_zona = None
                go("home")

        with c2:
            if st.button("Cancelar"):
                st.session_state.selected_type_id = None
                st.session_state.selected_type_name = None
                st.session_state.dist_car_carro = None
                st.session_state.dist_car_zona = None
                go("home")


# ============================================================
# EDIT
# ============================================================
elif st.session_state.screen == "edit":
    mid = st.session_state.edit_movement_id
    if not mid:
        st.warning("No hay movimiento para editar.")
        if st.button("Volver"):
            go("home")
    else:
        row = db.get_movement(int(mid))
        if not row:
            st.error("No se encontró ese movimiento.")
            if st.button("Volver"):
                go("home")
        else:
            st.subheader("✏️ Editar movimiento")
            st.caption(f"Hora guardada: {row['hhmmss']} (Europe/Madrid)")

            new_name = st.text_input("Nombre movimiento", value=row["movement_name"])
            new_comment = st.text_area("Comentario", value=row["comment"] or "", height=120)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 Guardar cambios"):
                    db.update_movement(int(mid), new_name, new_comment)
                    st.success("Actualizado ✅")
                    st.session_state.edit_movement_id = None
                    go("home")
            with c2:
                if st.button("🗑️ Eliminar"):
                    db.delete_movement(int(mid))
                    st.success("Eliminado ✅")
                    st.session_state.edit_movement_id = None
                    go("home")
            with c3:
                if st.button("Cancelar"):
                    st.session_state.edit_movement_id = None
                    go("home")


# ============================================================
# MANAGE
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
# PDF
# ============================================================
elif st.session_state.screen == "pdf":
    st.subheader("📄 Exportar a PDF")

    selected_day = st.date_input("Día a exportar", value=date.today())

    start_dt = datetime.combine(selected_day, time(0, 0, 0), tzinfo=MADRID)
    end_dt = datetime.combine(selected_day, time(23, 59, 59), tzinfo=MADRID)

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
    else:
        st.info("No hay movimientos ese día.")

    if st.button("Volver"):
        go("home")
