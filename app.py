import streamlit as st
import pandas as pd
import io
import plotly.express as px

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

st.write("### Productos Filtrados")
st.dataframe(filtro[["codigo", "producto", "unidad", "costo_neto", "margen_%", "precio_venta_iva"]])

# Ajuste de margen personalizado
nuevo_margen = st.slider("Ajusta el margen personalizado (%)", min_value=0, max_value=100, value=40)

if st.button("Aplicar nuevo margen personalizado"):
    filtro["nuevo_precio_venta"] = filtro["costo_neto"] * (1 + nuevo_margen / 100)
    filtro["nuevo_precio_venta_iva"] = (filtro["nuevo_precio_venta"] * 1.19).round(0)
    filtro["ganancia"] = filtro["nuevo_precio_venta"] - filtro["costo_neto"]

    st.write(f"### Nuevos precios con margen del {nuevo_margen}%")
    st.dataframe(filtro[["codigo", "producto", "costo_neto", "nuevo_precio_venta_iva", "ganancia"]])

    # Visualización gráfica
    fig = px.bar(
        filtro,
        x="producto",
        y=["costo_neto", "nuevo_precio_venta_iva"],
        barmode="group",
        title="Comparación de costos vs precios con IVA"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Crear el buffer Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        filtro.to_excel(writer, index=False)
    excel_buffer.seek(0)

    # Botón para descargar
    st.download_button(
        label=f"Descargar cotización para {cliente if cliente else 'cliente'}",
        data=excel_buffer,
        file_name=f"cotizacion_{cliente.replace(' ', '_') if cliente else 'sin_nombre'}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

