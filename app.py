import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime

st.set_page_config(page_title="Comercial Hanckes", layout="wide")

archivo_maestro = "formato_optimo_automatizacion.xlsx"
historial_dir = "historial_cotizaciones"
pedidos_dir = "pedidos_confirmados"
historial_clientes = "clientes_historial.xlsx"

os.makedirs(historial_dir, exist_ok=True)
os.makedirs(pedidos_dir, exist_ok=True)

if "pantalla" not in st.session_state:
    st.session_state.pantalla = "inicio"

def volver_al_inicio():
    st.session_state.pantalla = "inicio"

if st.session_state.pantalla == "inicio":
    st.title("💧 Comercial Hanckes - Menú Principal")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("🧮 Simular Precios", use_container_width=True):
            st.session_state.pantalla = "simulador"
    with col2:
        if st.button("📁 Ver Historial", use_container_width=True):
            st.session_state.pantalla = "historial"
    with col3:
        if st.button("✅ Pedidos Confirmados", use_container_width=True):
            st.session_state.pantalla = "pedidos"


# ------------------ SIMULADOR DE PRECIOS ------------------
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
            filtro.at[i, "cantidad"] = st.number_input(
                f"{row['producto']} (stock: {int(row['stock'])})",
                min_value=0, max_value=int(row["stock"]), step=1,
                key=f"sim_{i}"
            )

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

        with pd.ExcelWriter(os.path.join(historial_dir, filename), engine="openpyxl") as writer:
            filtro.to_excel(writer, index=False)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            filtro.to_excel(writer, index=False)
        buffer.seek(0)

        st.download_button("Descargar cotización", data=buffer, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)
# ------------------ HISTORIAL DE COTIZACIONES ------------------
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
            min_value=0, max_value=int(row["stock"]), step=1,
            key=f"pedido_{i}"
        )

    filtro["subtotal"] = filtro["precio_unitario"] * filtro["cantidad"]
    total = filtro["subtotal"].sum()
    iva = total * 0.19
    total_final = total + iva

    st.metric("Total Pedido", f"${total_final:,.0f}")
    st.dataframe(filtro[["producto", "cantidad", "precio_unitario", "subtotal", "stock"]])

    if st.button("✅ Confirmar Pedido"):
        if not cliente:
            st.error("Debe ingresar el nombre del cliente.")
        else:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
            pedido = filtro[filtro["cantidad"] > 0].copy()

            if pedido.empty:
                st.warning("Debe ingresar al menos un producto con cantidad mayor a 0.")
            else:
                pedido["cliente"] = cliente
                pedido["fecha"] = fecha
                pedido["estado_pago"] = "pendiente"

                pedido_name = f"pedido_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                pedido_path = os.path.join(pedidos_dir, pedido_name)
                with pd.ExcelWriter(pedido_path, engine="openpyxl") as writer:
                    pedido.to_excel(writer, index=False)

                df_actualizado = df.copy()
                alertas = []
                for i, row in pedido.iterrows():
                    idx = df_actualizado[df_actualizado["codigo"] == row["codigo"]].index
                    if not idx.empty:
                        df_actualizado.at[idx[0], "stock"] -= row["cantidad"]
                        nuevo_stock = df_actualizado.at[idx[0], "stock"]
                        if nuevo_stock < 10:
                            alertas.append(f"⚠️ Producto '{row['producto']}' con stock bajo: {nuevo_stock} unidades.")
                df_actualizado.to_excel(archivo_maestro, index=False)

                if os.path.exists(historial_clientes):
                    historial_df = pd.read_excel(historial_clientes)
                else:
                    historial_df = pd.DataFrame()

                pedido_historial = pedido[["cliente", "fecha", "producto", "cantidad", "precio_unitario", "subtotal"]]
                historial_df = pd.concat([historial_df, pedido_historial], ignore_index=True)
                historial_df.to_excel(historial_clientes, index=False)

                st.success("✅ Pedido confirmado, stock actualizado y cliente registrado.")
                for alerta in alertas:
                    st.warning(alerta)

    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)
# ------------------ SEGUIMIENTO DE PAGOS ------------------
if st.session_state.pantalla == "pagos":
    st.title("💰 Seguimiento de Pagos de Pedidos")

    filtro_estado = st.selectbox("Filtrar por estado", ["todos", "pendiente", "pagado"])
    archivos_pedidos = sorted(os.listdir(pedidos_dir), reverse=True)
    pedidos = []

    for archivo in archivos_pedidos:
        df_pedido = pd.read_excel(os.path.join(pedidos_dir, archivo))
        df_pedido["archivo"] = archivo
        pedidos.append(df_pedido)

    if pedidos:
        df_all = pd.concat(pedidos)
        if filtro_estado != "todos":
            df_all = df_all[df_all["estado_pago"].str.lower() == filtro_estado]

        pedidos_grouped = df_all.groupby(["archivo", "cliente", "fecha", "estado_pago"]).agg({
            "subtotal": "sum"
        }).reset_index()

        for _, row in pedidos_grouped.iterrows():
            st.markdown(f"""
                **Cliente:** {row['cliente']}  
                **Fecha:** {row['fecha']}  
                **Total:** ${row['subtotal']:,.0f}  
                **Estado:** {'✅ Pagado' if row['estado_pago'] == 'pagado' else '🔴 Pendiente'}
            """)

            if row['estado_pago'] == "pendiente":
                if st.button(f"Marcar como pagado - {row['archivo']}"):
                    path = os.path.join(pedidos_dir, row['archivo'])
                    df_update = pd.read_excel(path)
                    df_update["estado_pago"] = "pagado"
                    df_update["fecha_pago"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    df_update.to_excel(path, index=False)
                    st.success(f"Pedido {row['archivo']} marcado como pagado.")
                    st.experimental_rerun()

            st.markdown("---")
    else:
        st.info("No hay pedidos ingresados aún.")

    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)


# ------------------ HISTORIAL POR CLIENTE ------------------
if st.session_state.pantalla == "historial_cliente":
    st.title("📚 Historial por Cliente")

    if not os.path.exists(historial_clientes):
        st.info("No hay historial de clientes aún.")
    else:
        historial_df = pd.read_excel(historial_clientes)
        clientes_unicos = historial_df["cliente"].dropna().unique()
        cliente_sel = st.selectbox("Selecciona un cliente", clientes_unicos)

        cliente_df = historial_df[historial_df["cliente"] == cliente_sel]

        if cliente_df.empty:
            st.warning("Este cliente no tiene compras registradas.")
        else:
            st.write(f"### Compras realizadas por {cliente_sel}")
            st.dataframe(cliente_df[["fecha", "producto", "cantidad", "precio_unitario", "subtotal"]])

            total_comprado = cliente_df["subtotal"].sum()
            total_unidades = cliente_df["cantidad"].sum()
            total_productos = cliente_df["producto"].nunique()
            total_pedidos = cliente_df["fecha"].nunique()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🧾 Total pedidos", total_pedidos)
            col2.metric("📦 Productos distintos", total_productos)
            col3.metric("🔁 Unidades compradas", int(total_unidades))
            col4.metric("💸 Total gastado", f"${total_comprado:,.0f}")

            # Descargar historial
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                cliente_df.to_excel(writer, index=False)
            excel_buffer.seek(0)

            st.download_button(
                label=f"Descargar historial de {cliente_sel}",
                data=excel_buffer,
                file_name=f"historial_{cliente_sel.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.button("🔙 Volver al inicio", on_click=volver_al_inicio)

