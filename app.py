import streamlit as st
import pandas as pd
import io

# Cargar datos desde archivo Excel
df = pd.read_excel("formato_optimo_automatizacion.xlsx")

st.title("Simulador de Precios de Cloro - Comercial Hanckes")

# Filtros
canal = st.selectbox("Selecciona el canal de venta", df["canal"].unique())
proveedor = st.selectbox("Selecciona el proveedor", df["proveedor"].unique())
tipo = st.selectbox("Selecciona el tipo de producto", df["tipo_producto"].unique())

# Filtro de datos
filtro = df[(df["canal"] == canal) & (df["proveedor"] == proveedor) & (df["tipo_producto"] == tipo)]

st.write("### Productos Filtrados")
st.dataframe(filtro[["codigo", "producto", "unidad", "costo_neto", "margen_%", "precio_venta_iva"]])

# Ajuste de margen
nuevo_margen = st.slider("Ajusta el margen (%)", min_value=0, max_value=100, value=40)

if st.button("Aplicar nuevo margen"):
    filtro["nuevo_precio_venta"] = filtro["costo_neto"] * (1 + nuevo_margen / 100)
    filtro["nuevo_precio_venta_iva"] = (filtro["nuevo_precio_venta"] * 1.19).round(0)

    st.write("### Nuevos precios con margen del ", nuevo_margen, "%")
    st.dataframe(filtro[["codigo", "producto", "costo_neto", "nuevo_precio_venta_iva"]])

    # Crear el buffer Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        filtro.to_excel(writer, index=False)
    excel_buffer.seek(0)

    # Botón para descargar
    st.download_button(
        label="Descargar nuevos precios",
        data=excel_buffer,
        file_name="precios_actualizados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

