
# 💧 Simulador de Precios de Cloro - Comercial Hanckes

Este proyecto es una aplicación web construida con [Streamlit](https://streamlit.io/) que permite simular precios de productos de piscina (como cloro, reguladores de pH y alguicidas) para venta a clientes minoristas o mayoristas, ajustando márgenes y visualizando precios finales con IVA.

## 📦 Archivos incluidos

- `app.py`: Código fuente de la aplicación Streamlit
- `requirements.txt`: Dependencias necesarias para ejecutar la app
- `formato_optimo_automatizacion.xlsx`: Base de datos de productos en formato óptimo para automatización

## 🚀 ¿Qué permite hacer esta app?

- Filtrar productos por tipo, canal de venta y proveedor
- Visualizar precios base, márgenes y precios con IVA
- Ajustar márgenes deseados con un slider interactivo
- Calcular automáticamente nuevos precios
- Descargar tabla con precios actualizados

## ▶️ Cómo correr la app (en local)

1. Instala Streamlit si no lo tienes:

```bash
pip install streamlit pandas openpyxl
```

2. Ejecuta la aplicación:

```bash
streamlit run app.py
```

## ☁️ Cómo publicarla en Streamlit Cloud

1. Sube estos archivos a un repositorio de GitHub
2. Entra a [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Crea una nueva app vinculando tu repositorio
4. En el campo “main file” escribe `app.py` y haz clic en **Deploy**

---

Desarrollado para uso interno de **Comercial Hanckes**.
