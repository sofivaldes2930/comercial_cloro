import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime

st.set_page_config(page_title="Comercial Hanckes", layout="wide")

# Rutas
archivo_maestro = "formato_optimo_automatizacion.xlsx"
historial_dir = "historial_cotizaciones"
pedidos_dir = "pedidos_confirmados"

# Crear carpetas si no existen
os.makedirs(historial_dir, exist_ok=True)
os.makedirs(pedidos_dir, exist_ok=True)

# Inicializar pantalla
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "inicio"

def volver_al_inicio():
    st.session_state.pantalla = "inicio"

# ------------------ MENÚ PRINCIPAL ------------------
if st.session_state.pantalla == "inicio":
    st.title("💧 Comercial Hanckes - Menú Principal")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧮 Simular Precios", use_container_width=True):
            st.session_state.pantalla = "simulador"
    with col2:
        if st.button("📁 Ver Historial", use_container_width=True):
            st.session_state.pantalla = "historial"
    with col3:
        if st.button("✅ Pedidos Confirmados", use_container_width=True):
            st.session_state.pantalla = "pedidos"

# ------------------ SIMULADOR ------------------
if st.session_state.pantalla == "simulador":
    df = pd.read_excel(archivo_maestro)
    st.title("🧮 Simulador de Precios")

    cliente = st.text_input("Nombre del cliente")
    canal = st.selectbox("Canal", df["canal"].unique())
    proveedor = st.selectbox("Proveedor", df["proveedor"].unique())
    tipo = st.selectbox("Tipo de producto", df["tipo_producto"].unique())
    busqueda = st.text_input("Buscar producto")

    filtro = df[(df["canal"] == canal) & (df["proveedor"] == proveedor) & (df["tipo_producto"] == tipo)]
    if busqueda:
        filtro = filtro[filtro["producto"].str.contains(busqueda, case=False) | filtro["codigo"].str.contains(busqueda, case=False)]

    filtro["cantidad"] = 0
    st.dataframe(filtro[["codigo", "producto", "unidad", "stock", "costo_neto", "margen_%", "precio_venta_iva"]])

    nuevo_margen = st.number_input("Ingresa el margen personalizado (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.5)

    if st.button("Aplicar nuevo margen personalizado"):
        filtro["nuevo_precio_venta"] = filtro["costo_neto"] * (1 + nuevo_margen / 100)
        filtro["nuevo_precio_venta_iva"] = (filtro["nuevo_precio_venta"] * 1.19).round(0)
        filtro["ganancia_unitaria"] = filtro["nuevo_precio_venta"] - filtro["costo_neto"]

        for i, row in filtro.iterrows():
            filtro.at[i, "cantidad"] = st.number_input(f"{row['producto']} (stock: {int(row['stock'])})", min_value=0, max_value=int(row["stock"]), step=1)

        filtro["subtotal_neto"] = filtro["nuevo_precio_venta"] * filtro["cantidad"]
        filtro["subtotal_con_iva"] = filtro["nuevo_precio_venta_iva"] * filtro["cantidad"]
        filtro["ganancia_total"] = filtro["ganancia_unitaria"] * filtro["cantidad"]
        filtro["stock_restante"] = filtro["stock"] - filtro["cantidad"]

        st.metric("Total Neto", f"${filtro['subtotal_neto'].sum():,.0f}")
        st.metric("Total con IVA", f"${filtro['subtotal_con_iva'].sum():,.0f}")
        st.metric("Ganancia", f"${filtro['ganancia_total'].sum():,.0f}")

        st.dataframe(filtro[["codigo", "producto", "cantidad", "nuevo_precio_venta_iva", "subtotal_con_iva", "stock_restante"]])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        cliente_slug = cliente.replace(" ", "_") if cliente else "sin_nombre"
        filename = f"cotizacion_{cliente_slug}_{timestamp}.xlsx"

        # Guardar historial
        with pd.ExcelWriter(os.path.join(historial_dir, filename), engine="openpyxl") as writer:
            filtro.to_excel(writer, index=False)

        # Descargar
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            filtro.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("Descargar cotización", data=buffer, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)

# ------------------ HISTORIAL ------------------
if st.session_state.pantalla == "historial":
    st.title("📁 Historial de Cotizaciones")
    archivos = sorted(os.listdir(historial_dir), reverse=True)
    if archivos:
        seleccion = st.selectbox("Selecciona una cotización", archivos)
        with open(os.path.join(historial_dir, seleccion), "rb") as f:
            st.download_button("Descargar", f, file_name=seleccion)
    else:
        st.info("No hay cotizaciones todavía.")
    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)

# ------------------ PEDIDOS CONFIRMADOS ------------------
if st.session_state.pantalla == "pedidos":
    df = pd.read_excel(archivo_maestro)
    st.title("✅ Ingreso de Pedido Confirmado")

    cliente = st.text_input("Nombre del cliente *", placeholder="Ej: Supermercado Arauco")
    canal = st.selectbox("Canal", df["canal"].unique())
    proveedor = st.selectbox("Proveedor", df["proveedor"].unique())
    tipo = st.selectbox("Tipo de producto", df["tipo_producto"].unique())
    busqueda = st.text_input("Buscar producto")

    filtro = df[(df["canal"] == canal) & (df["proveedor"] == proveedor) & (df["tipo_producto"] == tipo)]
    if busqueda:
        filtro = filtro[filtro["producto"].str.contains(busqueda, case=False) | filtro["codigo"].str.contains(busqueda, case=False)]

    filtro["cantidad"] = 0
    filtro["precio_unitario"] = filtro["precio_venta_iva"]

    for i, row in filtro.iterrows():
        filtro.at[i, "cantidad"] = st.number_input(
            f"{row['producto']} (stock: {int(row['stock'])})",
            min_value=0, max_value=int(row["stock"]), step=1
        )

    filtro["subtotal"] = filtro["precio_unitario"] * filtro["cantidad"]
    total = filtro["subtotal"].sum()
    iva = total * 0.19
    total_final = total + iva

    st.metric("Total Pedido", f"${total_final:,.0f}")
    st.dataframe(filtro[["producto", "cantidad", "precio_unitario", "subtotal"]])

    if st.button("✅ Confirmar Pedido"):
        if not cliente:
            st.error("Debe ingresar el nombre del cliente.")
        else:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            pedido = filtro[filtro["cantidad"] > 0].copy()
            pedido["cliente"] = cliente
            pedido["fecha"] = fecha
            pedido["estado_pago"] = "pendiente"

            # Guardar pedido
            pedido_name = f"pedido_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            pedido_path = os.path.join(pedidos_dir, pedido_name)
            with pd.ExcelWriter(pedido_path, engine="openpyxl") as writer:
                pedido.to_excel(writer, index=False)

            # Actualizar stock en archivo maestro
            df_actualizado = df.copy()
            for i, row in pedido.iterrows():
                idx = df_actualizado[df_actualizado["codigo"] == row["codigo"]].index
                if not idx.empty:
                    df_actualizado.at[idx[0], "stock"] -= row["cantidad"]
            df_actualizado.to_excel(archivo_maestro, index=False)

            st.success("✅ Pedido confirmado y stock actualizado correctamente.")

    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)
