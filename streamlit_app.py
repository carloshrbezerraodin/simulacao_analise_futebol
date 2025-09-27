import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("⚽ Seleção de Atletas — Probabilidade de Participação em Gol (Série A)")

st.markdown("""
**Pergunta**: Quais jogadores têm maior probabilidade de participar de pelo menos 1 gol (gol ou assistência) no próximo jogo?  
Faça upload do arquivo **Dados Série A.xlsx** para rodar a análise.
""")

uploaded = st.file_uploader("📂 Upload do Excel", type=["xlsx", "xls", "csv"])
minutes_proj = st.slider("⏱️ Minutos projetados no próximo jogo", 45, 100, 90, step=5)

def load_df(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file, sheet_name=0)

if uploaded:
    df = load_df(uploaded)

    required = [
        "Player Name","Current Team","Time Played (m)","Expected Goals",
        "Open Play Expected Assists","Set Piece Expected Assists",
        "Opposition Cfg Xg Chance Quality"
    ]
    for c in required:
        if c not in df.columns:
            st.error(f"❌ Coluna obrigatória ausente: {c}")
            st.stop()

    df = df.copy()
    df["Expected Assists"] = df["Open Play Expected Assists"].fillna(0) + df["Set Piece Expected Assists"].fillna(0)
    df = df[df["Time Played (m)"] >= 270].copy()

    df["xG_per90"] = df["Expected Goals"].fillna(0) / (df["Time Played (m)"]/90.0)
    df["xA_per90"] = df["Expected Assists"] / (df["Time Played (m)"]/90.0)

    med = np.nanmedian(df["Opposition Cfg Xg Chance Quality"].values)
    if not np.isfinite(med) or med == 0:
        med = 1.0
    df["opp_factor"] = (df["Opposition Cfg Xg Chance Quality"] / med).clip(0.5, 1.5)

    df["lambda_match"] = (df["xG_per90"] + df["xA_per90"]) / df["opp_factor"] * (minutes_proj/90.0)
    df["p_gi>=1"] = 1 - np.exp(-df["lambda_match"])

    show_cols = [
        "Player Name","Current Team","xG_per90","xA_per90",
        "lambda_match","p_gi>=1","Opposition Cfg Xg Chance Quality","Time Played (m)"
    ]

    st.subheader("🏆 Top 10 jogadores")
    top10 = df.sort_values("p_gi>=1", ascending=False)[show_cols].head(10).round(3)
    st.dataframe(top10)

    # 🔽 botão para baixar CSV
    st.download_button(
        "⬇️ Baixar ranking completo (CSV)",
        df.sort_values("p_gi>=1", ascending=False)[show_cols].to_csv(index=False).encode("utf-8"),
        "ranking_participacao_gol.csv",
        "text/csv"
    )

    # 📊 Gráfico
    st.subheader("📊 Probabilidade de participação em gol (Top 10)")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.bar(top10["Player Name"], top10["p_gi>=1"], color="orange")
    ax.set_ylabel("Probabilidade (≥1 gol/assistência)")
    ax.set_xlabel("Jogadores")
    ax.set_title("Top 10 — Probabilidade de participação em gol")
    plt.xticks(rotation=30, ha="right")
    st.pyplot(fig)

else:
    st.info("⏳ Faça upload do arquivo Excel para rodar a análise.")
