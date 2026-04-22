import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


st.set_page_config(
    page_title="Dashboard de Ventas Supermarket Sales",
    layout="wide",
    initial_sidebar_state="expanded",
)

sns.set_theme(style="whitegrid")


@st.cache_data
def cargar_datos():
    df = pd.read_csv("data.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


df = cargar_datos()

st.title("Dashboard Interactivo de Ventas")
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fbff;
        border: 1px solid #d9e6f2;
        padding: 12px 14px;
        border-radius: 10px;
        min-height: 120px;
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricLabel"] p {
        font-size: 0.88rem;
        line-height: 1.2;
        white-space: normal !important;
        color: #1f2937 !important;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetricValue"] p {
        font-size: 1.05rem;
        line-height: 1.15;
        white-space: normal !important;
        color: #111827 !important;
    }
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] *,
    div[data-testid="stMetricDelta"] p {
        font-size: 0.82rem;
        white-space: normal !important;
        color: #059669 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Filtros")

fecha_min = df["Date"].min().date()
fecha_max = df["Date"].max().date()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max,
)

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas
else:
    fecha_inicio, fecha_fin = fecha_min, fecha_max

branch_options = sorted(df["Branch"].dropna().unique())
customer_options = sorted(df["Customer type"].dropna().unique())
product_options = sorted(df["Product line"].dropna().unique())
payment_options = sorted(df["Payment"].dropna().unique())

branch_mode = st.sidebar.selectbox(
    "Sucursal principal",
    ["Todas"] + branch_options,
)

customer_sel = st.sidebar.multiselect(
    "Tipo de cliente",
    customer_options,
    default=customer_options,
)

product_sel = st.sidebar.multiselect(
    "Linea de producto",
    product_options,
    default=product_options,
)

payment_sel = st.sidebar.multiselect(
    "Medio de pago",
    payment_options,
    default=payment_options,
)

rango_rating = st.sidebar.slider(
    "Rango de rating",
    min_value=float(df["Rating"].min()),
    max_value=float(df["Rating"].max()),
    value=(float(df["Rating"].min()), float(df["Rating"].max())),
    step=0.1,
)

metrica_producto = st.sidebar.radio(
    "Metrica para productos",
    ["Total", "Quantity", "gross income"],
    index=0,
)

mostrar_tendencia = st.sidebar.checkbox("Mostrar media movil", value=True)

df_filtrado = df[
    (df["Date"].dt.date >= fecha_inicio)
    & (df["Date"].dt.date <= fecha_fin)
    & (df["Customer type"].isin(customer_sel))
    & (df["Product line"].isin(product_sel))
    & (df["Payment"].isin(payment_sel))
    & (df["Rating"] >= rango_rating[0])
    & (df["Rating"] <= rango_rating[1])
].copy()

if branch_mode != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Branch"] == branch_mode]

if df_filtrado.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

def obtener_resumen_superior(dataframe):
    mejor_sucursal = (
        dataframe.groupby("Branch")["Rating"].mean().sort_values(ascending=False)
    )
    producto_top = (
        dataframe.groupby("Product line")["Total"].sum().sort_values(ascending=False)
    )

    return {
        "mejor_sucursal": mejor_sucursal.index[0],
        "rating_mejor_sucursal": mejor_sucursal.iloc[0],
        "producto_top": producto_top.index[0],
        "ventas_producto_top": producto_top.iloc[0],
    }


resumen_superior = obtener_resumen_superior(df_filtrado)

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Registros", f"{len(df_filtrado):,}")
col2.metric("Ventas totales", f"${df_filtrado['Total'].sum():,.2f}")
col3.metric("Ticket promedio", f"${df_filtrado['Total'].mean():,.2f}")
col4.metric("Satisfaccion promedio", f"{df_filtrado['Rating'].mean():.2f}/10")
col5.metric(
    "Sucursal mejor evaluada",
    resumen_superior["mejor_sucursal"],
    f"Satisfaccion {resumen_superior['rating_mejor_sucursal']:.2f}/10",
)
col6.metric(
    "Producto mas vendido",
    resumen_superior["producto_top"],
    f"Ventas ${resumen_superior['ventas_producto_top']:,.0f}",
)


def mostrar_linea_ventas(dataframe):
    ventas_diarias = (
        dataframe.groupby("Date", as_index=False)["Total"]
        .sum()
        .sort_values("Date")
    )
    ventas_diarias["Media movil 7 dias"] = ventas_diarias["Total"].rolling(7).mean()

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(ventas_diarias["Date"], ventas_diarias["Total"], color="#1f77b4", linewidth=2)
    if mostrar_tendencia:
        ax.plot(
            ventas_diarias["Date"],
            ventas_diarias["Media movil 7 dias"],
            color="#ff7f0e",
            linestyle="--",
            linewidth=2,
        )
    ax.set_title("Evolucion temporal de las ventas")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Total vendido")
    if mostrar_tendencia:
        ax.legend(["Ventas diarias", "Media movil 7 dias"])
    else:
        ax.legend(["Ventas diarias"])
    ax.grid(alpha=0.25)
    st.pyplot(fig, use_container_width=True)


def mostrar_barras_producto(dataframe):
    resumen = (
        dataframe.groupby("Product line")[metrica_producto]
        .sum()
        .sort_values(ascending=True)
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(resumen.index, resumen.values, color="#2a9d8f")
    ax.set_title(f"{metrica_producto} por linea de producto")
    ax.set_xlabel(metrica_producto)
    ax.set_ylabel("Linea de producto")
    st.pyplot(fig, use_container_width=True)


def mostrar_boxplot_clientes(dataframe):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.boxplot(data=dataframe, x="Customer type", y="Total", palette="Set2", ax=ax)
    ax.set_title("Distribucion del total por tipo de cliente")
    ax.set_xlabel("Tipo de cliente")
    ax.set_ylabel("Total por transaccion")
    st.pyplot(fig, use_container_width=True)


def mostrar_boxplot_rating(dataframe):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.boxplot(data=dataframe, x="Branch", y="Rating", palette="Pastel1", ax=ax)
    ax.set_title("Distribucion del rating por sucursal")
    ax.set_xlabel("Sucursal")
    ax.set_ylabel("Rating")
    st.pyplot(fig, use_container_width=True)


def mostrar_heatmap_sucursales(dataframe):
    resumen = dataframe.groupby("Branch", as_index=False).agg(
        Total=("Total", "sum"),
        Quantity=("Quantity", "sum"),
        Rating=("Rating", "mean"),
        GrossIncome=("gross income", "sum"),
    )

    metricas = resumen.set_index("Branch")
    metricas_normalizadas = (metricas - metricas.min()) / (metricas.max() - metricas.min())

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        metricas_normalizadas,
        annot=metricas.round(2),
        fmt="",
        cmap="YlOrRd",
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Radiografia multidimensional de sucursales")
    ax.set_xlabel("Metricas")
    ax.set_ylabel("Sucursal")
    st.pyplot(fig, use_container_width=True)


def mostrar_pago_segmentado(dataframe):
    tabla = pd.crosstab(dataframe["Customer type"], dataframe["Payment"])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    tabla.plot(kind="bar", stacked=True, ax=ax, color=["#264653", "#e76f51", "#e9c46a"])
    ax.set_title("Medios de pago por tipo de cliente")
    ax.set_xlabel("Tipo de cliente")
    ax.set_ylabel("Cantidad de transacciones")
    ax.legend(title="Pago", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig, use_container_width=True)


def mostrar_correlacion(dataframe):
    numericas = dataframe[
        [
            "Unit price",
            "Quantity",
            "Tax 5%",
            "Total",
            "cogs",
            "gross margin percentage",
            "gross income",
            "Rating",
        ]
    ]
    corr = numericas.corr()

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues", ax=ax)
    ax.set_title("Matriz de correlaciones")
    st.pyplot(fig, use_container_width=True)


def mostrar_grafico_libre(dataframe):
    resumen = pd.pivot_table(
        dataframe,
        values="Total",
        index="Product line",
        columns="Branch",
        aggfunc="sum",
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(resumen, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax)
    ax.set_title("Grafico libre: ventas por linea de producto y sucursal")
    ax.set_xlabel("Sucursal")
    ax.set_ylabel("Linea de producto")
    st.pyplot(fig, use_container_width=True)


st.subheader("Visualizaciones principales")
fila1_col1, fila1_col2 = st.columns([1.6, 1.1], gap="large")

with fila1_col1:
    mostrar_linea_ventas(df_filtrado)

with fila1_col2:
    mostrar_barras_producto(df_filtrado)

fila2_col1, fila2_col2 = st.columns(2, gap="large")

with fila2_col1:
    mostrar_boxplot_clientes(df_filtrado)

with fila2_col2:
    mostrar_boxplot_rating(df_filtrado)

fila3_col1, fila3_col2 = st.columns(2, gap="large")

with fila3_col1:
    mostrar_heatmap_sucursales(df_filtrado)

with fila3_col2:
    mostrar_pago_segmentado(df_filtrado)

st.subheader("Analisis complementario")
fila4_col1, fila4_col2 = st.columns(2, gap="large")

with fila4_col1:
    mostrar_correlacion(df_filtrado)

with fila4_col2:
    mostrar_grafico_libre(df_filtrado)
