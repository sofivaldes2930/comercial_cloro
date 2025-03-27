import streamlit as st
import pandas as pd
import io
import plotly.express as px
import os
from datetime import datetime

# Crear carpeta historial si no existe
historial_dir = "historial_cotizaciones"
os.makedirs(historial_dir, exist_ok=True)

# Tabs para navegación
menu = st.sidebar.radio("Menú", ["Simulador de Precios", "Historial de Cotizaciones", "Dashboard"])

if menu == "Simulador de Precios":
    # Cargar datos desde archivo Excel
    df = pd.read_excel("formato_optimo_automatizacion.xlsx")

    st.title("Simulador de Precios de Cloro - Comercial Hanckes")

    # Input de nombre del cliente
    cliente = st.text_input("Nombre del cliente para cotización")

    # Filtros
    canal = st.selectbox("Selecciona el canal de venta", df["canal"].unique())
    proveedor = st.selectbox("Selecciona el proveedor", df["proveedor"].unique())
    tipo = st.selectbox("Selecciona el tipo de producto", df["tipo_producto"].unique())

    # Campo de búsqueda por nombre o código
    busqueda = st.text_input("Buscar producto por nombre o código")

    # Filtro de datos
    filtro = df[(df["canal"] == canal) & (df["proveedor"] == proveedor) & (df["tipo_producto"] == tipo)]
    if busqueda:
        filtro = filtro[filtro["producto"].str.contains(busqueda, case=False) | filtro["codigo"].str.contains(busqueda, case=False)]

    filtro["cantidad"] = 0

    st.write("### Productos Filtrados")
st.dataframe(filtro[["codigo", "producto", "unidad", "stock", "costo_neto", "margen_%", "precio_venta_iva"]])

    nuevo_margen = st.number_input("Ingresa el margen personalizado (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.5)

    if st.button("Aplicar nuevo margen personalizado"):
        filtro["nuevo_precio_venta"] = filtro["costo_neto"] * (1 + nuevo_margen / 100)
        filtro["nuevo_precio_venta_iva"] = (filtro["nuevo_precio_venta"] * 1.19).round(0)
        filtro["ganancia_unitaria"] = filtro["nuevo_precio_venta"] - filtro["costo_neto"]

        st.write("### Ingrese cantidades para simular cotización")
        cantidades = {}
        error_stock = False

        for i, row in filtro.iterrows():
            cantidades[i] = st.number_input(f"{row['producto']} (stock: {int(row['stock'])})", min_value=0, max_value=int(row['stock']), step=1)
            filtro.at[i, "cantidad"] = cantidades[i]

        filtro["subtotal_neto"] = filtro["nuevo_precio_venta"] * filtro["cantidad"]
        filtro["subtotal_con_iva"] = filtro["nuevo_precio_venta_iva"] * filtro["cantidad"]
        filtro["ganancia_total"] = filtro["ganancia_unitaria"] * filtro["cantidad"]
        filtro["stock_restante"] = filtro["stock"] - filtro["cantidad"]

        total_neto = filtro["subtotal_neto"].sum()
        total_iva = total_neto * 0.19
        total_con_iva = total_neto + total_iva
        total_ganancia = filtro["ganancia_total"].sum()

        st.write("### Resumen de la Simulación")
        st.markdown(f"**Total Neto:** ${total_neto:,.0f}")
        st.markdown(f"**IVA (19%):** ${total_iva:,.0f}")
        st.markdown(f"**Total con IVA:** ${total_con_iva:,.0f}")
        st.markdown(f"**Ganancia estimada:** ${total_ganancia:,.0f}")

        st.write("### Detalle de Productos con Cantidades")
        st.dataframe(filtro[["codigo", "producto", "cantidad", "nuevo_precio_venta_iva", "subtotal_con_iva", "ganancia_total", "stock", "stock_restante"]])

        fig = px.bar(
            filtro,
            x="producto",
            y=["costo_neto", "nuevo_precio_venta_iva"],
            barmode="group",
            title="Comparación de costos vs precios con IVA"
        )
        st.plotly_chart(fig, use_container_width=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        cliente_slug = cliente.replace(" ", "_") if cliente else "sin_nombre"
        filename = f"cotizacion_{cliente_slug}_{timestamp}.xlsx"
        full_path = os.path.join(historial_dir, filename)

        with pd.ExcelWriter(full_path, engine="openpyxl") as writer:
            filtro.to_excel(writer, index=False)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            filtro.to_excel(writer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            label=f"Descargar cotización para {cliente if cliente else 'cliente'}",
            data=excel_buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif menu == "Historial de Cotizaciones":
    st.title("Historial de Cotizaciones Guardadas")
    archivos = sorted(os.listdir(historial_dir), reverse=True)
    seleccion = st.selectbox("Selecciona una cotización para descargar", archivos)
    ruta_archivo = os.path.join(historial_dir, seleccion)
    with open(ruta_archivo, "rb") as f:
        st.download_button("Descargar archivo seleccionado", f, file_name=seleccion)
    st.write("### Todas las cotizaciones disponibles")
    for archivo in archivos:
        st.markdown(f"- {archivo}")

elif menu == "Dashboard":
    st.title("Resumen de Cotizaciones")
    resumen = []
    for archivo in os.listdir(historial_dir):
        df_archivo = pd.read_excel(os.path.join(historial_dir, archivo))
        df_archivo["archivo"] = archivo
        resumen.append(df_archivo)
    if resumen:
        df_todo = pd.concat(resumen)
        total_cotizado = df_todo["subtotal_con_iva"].sum()
        total_productos = df_todo["cantidad"].sum()
        total_ganancia = df_todo["ganancia_total"].sum()

        st.metric("Total Cotizado", f"${total_cotizado:,.0f}")
        st.metric("Unidades Cotizadas", int(total_productos))
        st.metric("Ganancia Estimada", f"${total_ganancia:,.0f}")

        top_productos = df_todo.groupby("producto")["cantidad"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(top_productos)
    else:
        st.info("No hay cotizaciones en el historial todavía.")

