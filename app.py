import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(page_title="Nassau Candy Profitability Analysis", page_icon="🍬", layout="wide")

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    h1, h2, h3 {
        color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00D2D3;
    }
    .metric-label {
        font-size: 1rem;
        color: #A4B0BE;
    }
</style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv('Nassau Candy Distributor.csv')
    
    # Data Cleaning & Validation
    df = df[(df['Sales'] > 0) & (df['Cost'] > 0)]
    df = df[df['Units'] > 0]
    df['Units'] = df['Units'].fillna(1)
    df['Division'] = df['Division'].str.strip().str.title()
    df['Product Name'] = df['Product Name'].str.strip()
    
    # Date formatting
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    
    # Recalculate KPIs
    df['Gross Margin (%)'] = (df['Gross Profit'] / df['Sales']) * 100
    df['Profit per Unit'] = df['Gross Profit'] / df['Units']
    
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("🎯 Filter Options")

# Date range selector
min_date = df['Order Date'].min()
max_date = df['Order Date'].max()

# Handle potential NaT if dates couldn't be parsed
if pd.isna(min_date): min_date = datetime(2020, 1, 1)
if pd.isna(max_date): max_date = datetime(2030, 1, 1)

date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Division filter
divisions = ['All'] + list(df['Division'].unique())
selected_division = st.sidebar.selectbox("Select Division", divisions)

# Margin threshold slider
min_margin = float(df['Gross Margin (%)'].min())
max_margin = float(df['Gross Margin (%)'].max())
margin_threshold = st.sidebar.slider("Minimum Gross Margin (%)", min_value=min_margin, max_value=max_margin, value=min_margin)

# Product search
product_search = st.sidebar.text_input("Search Product Name (Optional)")

# Apply Filters
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df['Order Date'] >= pd.to_datetime(start_date)) & (filtered_df['Order Date'] <= pd.to_datetime(end_date))]

if selected_division != 'All':
    filtered_df = filtered_df[filtered_df['Division'] == selected_division]

filtered_df = filtered_df[filtered_df['Gross Margin (%)'] >= margin_threshold]

if product_search:
    filtered_df = filtered_df[filtered_df['Product Name'].str.contains(product_search, case=False, na=False)]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# --- Main Dashboard ---
st.title("🍬 Nassau Candy Distributor")
st.markdown("### Product Line Profitability & Margin Performance Dashboard")

# Top Level Metrics
total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Gross Profit'].sum()
avg_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">${total_sales:,.2f}</div><div class="metric-label">Total Sales</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value">${total_profit:,.2f}</div><div class="metric-label">Total Gross Profit</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_margin:.2f}%</div><div class="metric-label">Avg Gross Margin</div></div>', unsafe_allow_html=True)

st.divider()

# --- Module 1: Product Profitability Overview ---
st.header("🏆 Product Profitability Overview")

product_group = filtered_df.groupby('Product Name').agg({
    'Sales': 'sum', 'Gross Profit': 'sum'
}).reset_index()
product_group['Gross Margin (%)'] = (product_group['Gross Profit'] / product_group['Sales']) * 100
product_group['Profit Contribution (%)'] = (product_group['Gross Profit'] / total_profit) * 100

col_p1, col_p2 = st.columns(2)
with col_p1:
    st.subheader("Margin Leaderboard (Top 10)")
    top_products = product_group.sort_values('Gross Margin (%)', ascending=False).head(10)
    fig_leaderboard = px.bar(top_products, y='Product Name', x='Gross Margin (%)', orientation='h',
                             color='Gross Margin (%)', color_continuous_scale='Mint', title="Top Products by Margin")
    fig_leaderboard.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_leaderboard, use_container_width=True)

with col_p2:
    st.subheader("Profit Contribution")
    top_contrib = product_group.sort_values('Profit Contribution (%)', ascending=False).head(10)
    fig_contrib = px.pie(top_contrib, values='Profit Contribution (%)', names='Product Name', 
                         title="Top 10 Products by Profit Contribution", hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
    st.plotly_chart(fig_contrib, use_container_width=True)


# --- Module 2: Division Performance Dashboard ---
st.header("🏢 Division Performance Dashboard")

div_group = filtered_df.groupby('Division').agg({'Sales': 'sum', 'Gross Profit': 'sum'}).reset_index()

col_d1, col_d2 = st.columns(2)
with col_d1:
    fig_div_compare = go.Figure()
    fig_div_compare.add_trace(go.Bar(x=div_group['Division'], y=div_group['Sales'], name='Revenue', marker_color='#3498db'))
    fig_div_compare.add_trace(go.Bar(x=div_group['Division'], y=div_group['Gross Profit'], name='Gross Profit', marker_color='#2ecc71'))
    fig_div_compare.update_layout(title="Revenue vs Profit Comparison", barmode='group')
    st.plotly_chart(fig_div_compare, use_container_width=True)
    
with col_d2:
    fig_box = px.box(filtered_df, x='Division', y='Gross Margin (%)', color='Division', 
                     title="Margin Distribution by Division")
    st.plotly_chart(fig_box, use_container_width=True)


# --- Module 3: Cost vs Margin Diagnostics ---
st.header("📉 Cost vs Margin Diagnostics")

col_c1, col_c2 = st.columns([2, 1])
with col_c1:
    fig_scatter = px.scatter(filtered_df, x='Sales', y='Cost', color='Gross Margin (%)',
                             hover_data=['Product Name', 'Division'],
                             color_continuous_scale='Turbo', title="Cost vs Sales Scatter Plot (Order Level)")
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_c2:
    st.subheader("Margin Risk Flags")
    # Identify items where Cost > Sales (Negative Margin) or Margin < 10%
    risk_products = product_group[product_group['Gross Margin (%)'] < 10].sort_values('Gross Margin (%)')
    if not risk_products.empty:
        st.error(f"Found {len(risk_products)} products with <10% Margin.")
        st.dataframe(risk_products[['Product Name', 'Gross Margin (%)', 'Gross Profit']].style.format({"Gross Margin (%)": "{:.2f}%", "Gross Profit": "${:.2f}"}))
    else:
        st.success("No significant margin risks detected in current view.")


# --- Module 4: Profit Concentration Analysis ---
st.header("📊 Profit Concentration Analysis")

# Pareto Analysis
pareto_df = product_group.sort_values(by='Gross Profit', ascending=False).copy()
pareto_df['Cumulative Profit (%)'] = 100 * (pareto_df['Gross Profit'].cumsum() / pareto_df['Gross Profit'].sum())

# Identify 80% contributors
num_products_80 = len(pareto_df[pareto_df['Cumulative Profit (%)'] <= 80])
total_products = len(pareto_df)
st.info(f"**Dependency Indicator**: {num_products_80} out of {total_products} products ({num_products_80/total_products*100:.1f}%) contribute to 80% of the total profit.")

fig_pareto = go.Figure()
fig_pareto.add_trace(go.Bar(x=pareto_df['Product Name'], y=pareto_df['Gross Profit'], name='Gross Profit', marker_color='#9b59b6'))
fig_pareto.add_trace(go.Scatter(x=pareto_df['Product Name'], y=pareto_df['Cumulative Profit (%)'], name='Cumulative %', yaxis='y2', line=dict(color='#e74c3c', width=3)))

fig_pareto.update_layout(
    title="Pareto Chart - Profit Concentration",
    yaxis=dict(title='Gross Profit'),
    yaxis2=dict(title='Cumulative Profit (%)', overlaying='y', side='right', range=[0, 105]),
    showlegend=True
)
st.plotly_chart(fig_pareto, use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #7f8c8d;'>Powered by Streamlit | Developed for Nassau Candy Distributor</div>", unsafe_allow_html=True)
