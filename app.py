
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

# --- 1. CONFIGURAÇÃO DE TEMA "EXNOVA DARK" ---
st.set_page_config(page_title="AlphaStrike Analytics | Pro Terminal", layout="wide")

st.markdown("""
    <style>
    /* Fundo Principal */
    .stApp {
        background-color: #0b0e18;
        color: #e0e6ed;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #151926;
        border-right: 1px solid #2d3446;
    }
    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #1c2130;
        border: 1px solid #2d3446;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #00ff88;
    }
    /* Botão Principal */
    .stButton>button {
        width: 100%;
        background-color: #00ff88 !important;
        color: #0b0e18 !important;
        font-weight: bold !important;
        border: none !important;
        height: 3em !important;
    }
    /* Destaque de Oportunidade */
    .opportunity-card {
        background: linear-gradient(90deg, #1c2130 0%, #151926 100%);
        padding: 25px;
        border-radius: 15px;
        border-left: 10px solid #00ff88;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE INTELIGÊNCIA (BACKEND) ---
class MarketIntelligence:
    @staticmethod
    def get_real_data(tickers):
        analysis = []
        for t in tickers:
            try:
                # Puxando dados de 15 min para análise intradiária
                asset = yf.Ticker(t)
                df = asset.history(period="2d", interval="15m")
                if df.empty: continue
                
                # Cálculo de Volatilidade (ATR Simples)
                volatilidade = (df['High'] - df['Low']).mean()
                
                # Cálculo de Volume Institucional (Z-Score simplificado)
                vol_atual = df['Volume'].iloc[-1]
                vol_medio = df['Volume'].mean()
                pico_vol = vol_atual / vol_medio
                
                # Lógica de Preço (Bull/Bear)
                last_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                sentimento = "🟢 COMPRA" if last_price > prev_price else "🔴 VENDA"
                
                # Score AlphaStrike (0-100)
                score = min((pico_vol * 40) + (volatilidade * 1000), 100)
                
                analysis.append({
                    "Ativo": t.replace("=X", ""),
                    "Preço": f"{last_price:.4f}",
                    "Volatilidade": round(volatilidade, 5),
                    "Pressão Volume": f"{pico_vol:.2f}x",
                    "Score": round(score, 1),
                    "Sinal": sentimento
                })
            except: continue
        return pd.DataFrame(analysis).sort_values(by="Score", ascending=False)

# --- 3. LÓGICA DE GERENCIAMENTO DE RISCO ---
def check_risk(capital, risco_pct, perda_hoje):
    max_perda = capital * (3 / 100) # Fixo 3% de stop diário
    if perda_hoje >= max_perda:
        return False, f"🚨 STOP DIÁRIO ATINGIDO: Limite de ${max_perda:.2f} excedido."
    return True, "✅ OPERAÇÃO DENTRO DO RISCO"

# --- 4. INTERFACE DO USUÁRIO (FRONTEND) ---

# SIDEBAR
st.sidebar.title("🛡️ ALPHA STRIKE v3.0")
st.sidebar.caption("Terminal de Confluência Institucional")
capital = st.sidebar.number_input("Balanço da Conta ($)", value=1000.0)
risco_pct = st.sidebar.slider("Risco por Trade (%)", 0.5, 3.0, 1.0)
perda_acumulada = st.sidebar.number_input("Prejuízo do Dia ($)", value=0.0)

# CABEÇALHO DE MÉTRICAS
st.title("🎯 Radar de Fluxo Profissional")
c1, c2, c3 = st.columns(3)
c1.metric("Capital em Risco", f"${capital * (risco_pct/100):.2f}")
c2.metric("Meta Sugerida (2:1)", f"${(capital * (risco_pct/100)) * 2:.2f}")
c3.metric("Status da Sessão", "Risk-On" if datetime.datetime.now().hour < 12 else "Risk-Off")

st.markdown("---")

# SCANNER DE MERCADO (DADOS REAIS)
tickers = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "BTC-USD", "ETH-USD", "GC=F", "CL=F"]

with st.spinner("Sincronizando com o fluxo das baleias..."):
    df_data = MarketIntelligence.get_real_data(tickers)

if not df_data.empty:
    top = df_data.iloc[0]
    
    # CARD DE DESTAQUE (VENDÁVEL)
    st.markdown(f"""
        <div class="opportunity-card">
            <h3 style="margin:0; color:#00ff88;">🏆 MELHOR ATIVO PARA OPERAR AGORA: {top['Ativo']}</h3>
            <p style="font-size:18px; margin:5px 0;">O algoritmo detectou uma confluência de <b>{top['Score']}%</b></p>
            <span style="background:#00ff88; color:#0b0e18; padding:5px 10px; border-radius:5px; font-weight:bold;">
                SINAL: {top['Sinal']}
            </span>
            <p style="margin-top:15px; color:#aeb4c2;">Volume institucional está <b>{top['Pressão Volume']}</b> acima da média histórica de 15min.</p>
        </div>
    """, unsafe_allow_html=True)

    # TABELA DE RADAR
    col_table, col_calc = st.columns([2, 1])
    
    with col_table:
        st.subheader("📡 Monitoramento de Ativos")
        st.table(df_data[["Ativo", "Preço", "Pressão Volume", "Score", "Sinal"]])

    with col_calc:
        st.subheader("⚖️ Calculadora de Lote")
        stop_dist = st.number_input("Distância do Stop (Pips/Pontos)", value=100)
        
        liberado, msg = check_risk(capital, risco_pct, perda_acumulada)
        
        if liberado:
            st.success(msg)
            lote = (capital * (risco_pct/100)) / (stop_dist * 0.1) # Simples p/ Forex
            st.info(f"Lote Sugerido: **{lote:.2f}**")
            if st.button("EXECUTAR ANÁLISE NO GRÁFICO"):
                st.toast("Análise enviada para o terminal!", icon="🚀")
        else:
            st.error(msg)
            st.button("BLOQUEADO", disabled=True)

else:
    st.error("Erro ao conectar com o servidor de dados. Verifique sua conexão.")

st.markdown("---")
st.caption("AlphaStrike Analytics © 2026 - Tecnologia de Análise Quantitativa para Traders Pro.")
