import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Indian Personal Finance Dashboard",
    page_icon="₹",
    layout="wide"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .metric-label { font-size: 13px !important; }
    </style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df["Age_Group"] = pd.cut(
        df["Age"],
        bins=[17, 25, 35, 50, 65],
        labels=["18–25", "26–35", "36–50", "51–64"]
    )
    df["Total_Expenses"] = df[[
        "Rent", "Loan_Repayment", "Insurance", "Groceries",
        "Transport", "Eating_Out", "Entertainment", "Utilities",
        "Healthcare", "Education", "Miscellaneous"
    ]].sum(axis=1)
    df["Total_Potential_Savings"] = df[[
        "Potential_Savings_Groceries", "Potential_Savings_Transport",
        "Potential_Savings_Eating_Out", "Potential_Savings_Entertainment",
        "Potential_Savings_Utilities", "Potential_Savings_Healthcare",
        "Potential_Savings_Education", "Potential_Savings_Miscellaneous"
    ]].sum(axis=1)
    df["Savings_Gap"] = df["Desired_Savings"] - df["Disposable_Income"]
    return df

df = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🇮🇳 Indian Personal Finance & Spending Dashboard")
st.caption("Explore income, expenses, savings patterns across 20,000 individuals. Use filters to drill down.")

st.divider()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

city_options = ["All"] + sorted(df["City_Tier"].unique().tolist())
occ_options  = ["All"] + sorted(df["Occupation"].unique().tolist())
age_options  = ["All"] + df["Age_Group"].cat.categories.tolist()
dep_options  = ["All"] + sorted(df["Dependents"].unique().tolist())

city_filter = st.sidebar.selectbox("City Tier", city_options)
occ_filter  = st.sidebar.selectbox("Occupation", occ_options)
age_filter  = st.sidebar.selectbox("Age Group", age_options)
dep_filter  = st.sidebar.selectbox("Dependents", dep_options)

income_min, income_max = int(df["Income"].min()), int(df["Income"].max())
income_range = st.sidebar.slider(
    "Income range (₹)", income_min, income_max,
    (income_min, income_max), step=1000
)

# Apply filters
mask = (
    (df["Income"] >= income_range[0]) &
    (df["Income"] <= income_range[1])
)
if city_filter != "All": mask &= df["City_Tier"] == city_filter
if occ_filter  != "All": mask &= df["Occupation"] == occ_filter
if age_filter  != "All": mask &= df["Age_Group"].astype(str) == age_filter
if dep_filter  != "All": mask &= df["Dependents"] == dep_filter

filtered = df[mask]

st.sidebar.markdown(f"**{len(filtered):,}** individuals selected")

if filtered.empty:
    st.warning("No data matches the selected filters. Please adjust your filters.")
    st.stop()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

avg_income     = filtered["Income"].mean()
avg_expense    = filtered["Total_Expenses"].mean()
avg_disposable = filtered["Disposable_Income"].mean()
avg_savings    = filtered["Desired_Savings"].mean()
avg_potential  = filtered["Total_Potential_Savings"].mean()

k1.metric("Avg Monthly Income",    f"₹{avg_income:,.0f}")
k2.metric("Avg Total Expenses",    f"₹{avg_expense:,.0f}",
          delta=f"{(avg_expense/avg_income*100):.1f}% of income", delta_color="inverse")
k3.metric("Avg Disposable Income", f"₹{avg_disposable:,.0f}")
k4.metric("Avg Desired Savings",   f"₹{avg_savings:,.0f}")
k5.metric("Avg Potential Savings", f"₹{avg_potential:,.0f}", delta="if habits improve")

st.divider()

# ── Row 1: Spending breakdown + Income vs Expenses by Tier ────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Where does money go?")
    expense_cols = {
        "Rent": "Rent", "Loan Repayment": "Loan_Repayment",
        "Insurance": "Insurance", "Groceries": "Groceries",
        "Transport": "Transport", "Eating Out": "Eating_Out",
        "Entertainment": "Entertainment", "Utilities": "Utilities",
        "Healthcare": "Healthcare", "Education": "Education",
        "Miscellaneous": "Miscellaneous"
    }
    avg_expenses = {label: filtered[col].mean() for label, col in expense_cols.items()}
    fig1 = px.pie(
        names=list(avg_expenses.keys()),
        values=list(avg_expenses.values()),
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    fig1.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=350)
    st.plotly_chart(fig1, use_container_width=True)
    st.caption("Average spend distribution across all expense categories in the filtered group.")

with col2:
    st.subheader("Income vs Expenses by City Tier")
    tier_group = filtered.groupby("City_Tier")[["Income", "Total_Expenses", "Disposable_Income"]].mean().reset_index()
    tier_group.columns = ["City Tier", "Avg Income", "Avg Expenses", "Avg Disposable"]
    fig2 = go.Figure()
    fig2.add_bar(name="Avg Income",    x=tier_group["City Tier"], y=tier_group["Avg Income"],    marker_color="#3266ad")
    fig2.add_bar(name="Avg Expenses",  x=tier_group["City Tier"], y=tier_group["Avg Expenses"],  marker_color="#D85A30")
    fig2.add_bar(name="Avg Disposable",x=tier_group["City Tier"], y=tier_group["Avg Disposable"],marker_color="#1D9E75")
    fig2.update_layout(
        barmode="group", height=350,
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis_tickprefix="₹", yaxis_tickformat=",",
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Higher-tier cities earn more but also spend significantly more — Tier 3 has better disposable ratios.")

st.divider()

# ── Row 2: Potential savings + Savings gap ────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Where can people save more?")
    pot_cols = {
        "Groceries": "Potential_Savings_Groceries",
        "Transport": "Potential_Savings_Transport",
        "Eating Out": "Potential_Savings_Eating_Out",
        "Entertainment": "Potential_Savings_Entertainment",
        "Utilities": "Potential_Savings_Utilities",
        "Healthcare": "Potential_Savings_Healthcare",
        "Education": "Potential_Savings_Education",
        "Miscellaneous": "Potential_Savings_Miscellaneous"
    }
    pot_avgs = {label: filtered[col].mean() for label, col in pot_cols.items()}
    pot_df = pd.DataFrame({"Category": pot_avgs.keys(), "Potential Savings": pot_avgs.values()})
    pot_df = pot_df.sort_values("Potential Savings", ascending=True)
    fig3 = px.bar(
        pot_df, x="Potential Savings", y="Category", orientation="h",
        color="Potential Savings", color_continuous_scale="Teal",
        text_auto=".0f"
    )
    fig3.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside")
    fig3.update_layout(
        height=340, margin=dict(t=10, b=10, l=10, r=60),
        coloraxis_showscale=False,
        xaxis_tickprefix="₹", xaxis_tickformat=","
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Groceries and Transport offer the highest potential savings on average.")

with col4:
    st.subheader("Desired savings vs Disposable income")
    occ_group = filtered.groupby("Occupation")[["Desired_Savings", "Disposable_Income"]].mean().reset_index()
    fig4 = px.scatter(
        occ_group, x="Disposable_Income", y="Desired_Savings",
        text="Occupation", size_max=20,
        color="Occupation",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig4.update_traces(textposition="top center", marker=dict(size=16))
    fig4.add_shape(type="line",
        x0=occ_group["Disposable_Income"].min(), y0=occ_group["Disposable_Income"].min(),
        x1=occ_group["Disposable_Income"].max(), y1=occ_group["Disposable_Income"].max(),
        line=dict(dash="dot", color="gray", width=1)
    )
    fig4.update_layout(
        height=340, margin=dict(t=10, b=10, l=10, r=10),
        xaxis_tickprefix="₹", xaxis_tickformat=",",
        yaxis_tickprefix="₹", yaxis_tickformat=",",
        showlegend=False
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.caption("Points above the dotted line = desired savings exceed disposable income — a financial stress signal.")

st.divider()

# ── Row 3: Expense by Occupation (stacked) + Age group income ─────────────────
col5, col6 = st.columns(2)

with col5:
    st.subheader("Expense structure by occupation")
    top_cats = ["Rent", "Loan_Repayment", "Groceries", "Transport", "Eating_Out", "Miscellaneous"]
    cat_labels = ["Rent", "Loan", "Groceries", "Transport", "Eating Out", "Misc"]
    occ_stack = filtered.groupby("Occupation")[top_cats].mean().reset_index()
    fig5 = go.Figure()
    colors = ["#3266ad","#D85A30","#1D9E75","#D4537E","#BA7517","#73726c"]
    for col_name, label, clr in zip(top_cats, cat_labels, colors):
        fig5.add_bar(name=label, x=occ_stack["Occupation"], y=occ_stack[col_name], marker_color=clr)
    fig5.update_layout(
        barmode="stack", height=340,
        margin=dict(t=10, b=10, l=10, r=10),
        yaxis_tickprefix="₹", yaxis_tickformat=",",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11))
    )
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("Self-employed and professionals carry higher rent and loan burdens.")

with col6:
    st.subheader("Income & savings across age groups")
    age_group_data = filtered.groupby("Age_Group", observed=True)[["Income", "Desired_Savings", "Disposable_Income"]].mean().reset_index()
    fig6 = go.Figure()
    fig6.add_scatter(x=age_group_data["Age_Group"].astype(str), y=age_group_data["Income"],
                     mode="lines+markers", name="Avg Income", line=dict(color="#3266ad", width=2), marker=dict(size=8))
    fig6.add_scatter(x=age_group_data["Age_Group"].astype(str), y=age_group_data["Desired_Savings"],
                     mode="lines+markers", name="Desired Savings", line=dict(color="#1D9E75", width=2, dash="dash"), marker=dict(size=8))
    fig6.add_scatter(x=age_group_data["Age_Group"].astype(str), y=age_group_data["Disposable_Income"],
                     mode="lines+markers", name="Disposable Income", line=dict(color="#D85A30", width=2, dash="dot"), marker=dict(size=8))
    fig6.update_layout(
        height=340, margin=dict(t=10, b=10, l=10, r=10),
        yaxis_tickprefix="₹", yaxis_tickformat=",",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11))
    )
    st.plotly_chart(fig6, use_container_width=True)
    st.caption("Income peaks in the 36–50 group. Watch whether savings aspirations keep up with rising expenses.")

st.divider()

# ── Row 4: Dependents impact + Savings % distribution ─────────────────────────
col7, col8 = st.columns(2)

with col7:
    st.subheader("How dependents affect disposable income")
    dep_data = filtered.groupby("Dependents")[["Income", "Total_Expenses", "Disposable_Income"]].mean().reset_index()
    fig7 = px.bar(
        dep_data, x="Dependents", y=["Income", "Total_Expenses", "Disposable_Income"],
        barmode="group",
        color_discrete_map={"Income":"#3266ad","Total_Expenses":"#D85A30","Disposable_Income":"#1D9E75"}
    )
    fig7.update_layout(
        height=320, margin=dict(t=10, b=10, l=10, r=10),
        yaxis_tickprefix="₹", yaxis_tickformat=",",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        xaxis_title="Number of dependents"
    )
    st.plotly_chart(fig7, use_container_width=True)
    st.caption("More dependents = higher expenses and lower disposable income even at similar income levels.")

with col8:
    st.subheader("Desired savings % distribution")
    fig8 = px.histogram(
        filtered, x="Desired_Savings_Percentage",
        nbins=30, color_discrete_sequence=["#534AB7"]
    )
    fig8.update_layout(
        height=320, margin=dict(t=10, b=10, l=10, r=10),
        xaxis_title="Desired savings %",
        yaxis_title="Number of individuals",
        xaxis_tickformat=".0%"
    )
    st.plotly_chart(fig8, use_container_width=True)
    st.caption("Most people target 10–20% savings. A long tail shows ambitious savers aiming for 30%+.")

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.caption("Dashboard built with Streamlit + Plotly · Dataset: 20,000 Indian individuals · All amounts in ₹")