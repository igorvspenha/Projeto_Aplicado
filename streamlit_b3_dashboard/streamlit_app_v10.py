
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import backtrader as bt
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Backtesting B3", layout="wide")
st.markdown("## 📊 Backtesting de Estratégias Quantitativas – Ibovespa")

# Lista de ações do Ibovespa
acoes_ibov = sorted([
    'ABEV3.SA', 'ALPA4.SA', 'AMER3.SA', 'ASAI3.SA', 'AZUL4.SA', 'B3SA3.SA', 'BBAS3.SA',
    'BBDC4.SA', 'BBSE3.SA', 'BPAC11.SA', 'BRFS3.SA', 'BRKM5.SA', 'CIEL3.SA', 'CMIG4.SA',
    'COGN3.SA', 'CPLE6.SA', 'CSAN3.SA', 'CSNA3.SA', 'CYRE3.SA', 'DXCO3.SA', 'ELET3.SA',
    'EMBR3.SA', 'ENEV3.SA', 'EQTL3.SA', 'GGBR4.SA', 'GOAU4.SA', 'HAPV3.SA', 'HYPE3.SA',
    'IRBR3.SA', 'ITSA4.SA', 'ITUB4.SA', 'JBSS3.SA', 'LREN3.SA', 'MGLU3.SA', 'MRFG3.SA',
    'MULT3.SA', 'NTCO3.SA', 'PETR4.SA', 'PRIO3.SA', 'RAIL3.SA', 'RENT3.SA', 'SBSP3.SA',
    'SUZB3.SA', 'TAEE11.SA', 'TOTS3.SA', 'UGPA3.SA', 'USIM5.SA', 'VALE3.SA', 'VIVT3.SA', 'WEGE3.SA'
])

# Estratégias com nomes descritivos
estrategias = {
    "Médias Móveis com Volatilidade": "StrategyMovingAverageVolatility",
    "RSI com MACD": "StrategyRSIMACD",
    "Bollinger + Volume": "StrategyBollingerVolume",
    "Z-Score com Reversão à Média": "StrategyZScoreMeanReversion",
    "Momentum com Stop e Gain": "StrategyMomentumTrailing",
    "MACD Cruzamento Clássico": "StrategyMACDCross",
    "RSI Simples": "StrategySimpleRSI",
    "Canal de Donchian": "StrategyDonchianChannel",
    "ADX Direcional": "StrategyADXTrend",
    "Estocástico Lento": "StrategyStochasticSlow"
}

# Seções da interface
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/30/B3_logo.png", width=150)
    ativos = st.multiselect('📈 Escolha até 3 ações:', acoes_ibov, default=['PETR4.SA', 'VALE3.SA'])
    estrategia_nome = st.selectbox('🧠 Escolha a estratégia:', list(estrategias.keys()))
    data_inicio = st.date_input('📅 Data de Início:', datetime(2018, 1, 1))
    data_fim = st.date_input('📅 Data de Fim:', datetime(2024, 12, 31))
    executar = st.button("🚀 Rodar Backtest")

# Estratégias base
class StrategyMovingAverageVolatility(bt.Strategy):
    params = dict(fast=10, slow=30, vol_window=20, vol_threshold=0.02)
    def __init__(self):
        self.ma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast)
        self.ma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow)
        self.returns = bt.indicators.PercentChange(self.data.close)
        self.volatility = bt.indicators.StandardDeviation(self.returns, period=self.p.vol_window)
    def next(self):
        if not self.position and self.ma_fast[0] > self.ma_slow[0] and self.volatility[0] > self.p.vol_threshold:
            self.buy()
        elif self.ma_fast[0] < self.ma_slow[0]:
            self.close()

class StrategyRSIMACD(bt.Strategy):
    def __init__(self):
        self.rsi = bt.ind.RSI(self.data.close, period=14)
        self.macd = bt.ind.MACD(self.data.close)
    def next(self):
        if not self.position and self.rsi[0] < 30 and self.macd.macd[0] > self.macd.signal[0]:
            self.buy()
        elif self.rsi[0] > 70:
            self.close()

class StrategyBollingerVolume(bt.Strategy):
    def __init__(self):
        self.bb = bt.ind.BollingerBands(self.data.close, period=20)
        self.vol_avg = bt.ind.SMA(self.data.volume, period=20)
    def next(self):
        if not self.position and self.data.close[0] < self.bb.lines.bot[0] and self.data.volume[0] > self.vol_avg[0]:
            self.buy()
        elif self.data.close[0] > self.bb.lines.mid[0]:
            self.close()

class StrategyZScoreMeanReversion(bt.Strategy):
    def __init__(self):
        self.ema = bt.ind.EMA(self.data.close, period=20)
        self.std = bt.ind.StandardDeviation(self.data.close, period=20)
    def next(self):
        z = (self.data.close[0] - self.ema[0]) / self.std[0]
        if not self.position and z < -2:
            self.buy()
        elif z > 0:
            self.close()

class StrategyMomentumTrailing(bt.Strategy):
    params = dict(momentum_period=15, stop_loss=0.05, take_profit=0.10)
    def __init__(self):
        self.momentum = bt.ind.ROC(self.data.close, period=self.p.momentum_period)
        self.entry_price = None
    def next(self):
        if not self.position and self.momentum[0] > 0:
            self.buy()
            self.entry_price = self.data.close[0]
        elif self.entry_price:
            if self.data.close[0] < self.entry_price * (1 - self.p.stop_loss) or self.data.close[0] > self.entry_price * (1 + self.p.take_profit):
                self.close()

# Estratégias extras
class StrategyMACDCross(bt.Strategy):
    def __init__(self):
        self.macd = bt.ind.MACD(self.data)
    def next(self):
        if not self.position and self.macd.macd[0] > self.macd.signal[0]:
            self.buy()
        elif self.macd.macd[0] < self.macd.signal[0]:
            self.close()

class StrategySimpleRSI(bt.Strategy):
    def __init__(self):
        self.rsi = bt.ind.RSI_SMA(self.data.close, period=14)
    def next(self):
        if not self.position and self.rsi[0] < 30:
            self.buy()
        elif self.rsi[0] > 70:
            self.close()

class StrategyDonchianChannel(bt.Strategy):
    def __init__(self):
        self.high = bt.ind.Highest(self.data.high, period=20)
        self.low = bt.ind.Lowest(self.data.low, period=20)
    def next(self):
        if not self.position and self.data.close[0] > self.high[-1]:
            self.buy()
        elif self.data.close[0] < self.low[-1]:
            self.close()

class StrategyADXTrend(bt.Strategy):
    def __init__(self):
        self.adx = bt.ind.ADX(self.data)
    def next(self):
        if not self.position and self.adx[0] > 25:
            self.buy()
        elif self.adx[0] < 20:
            self.close()

class StrategyStochasticSlow(bt.Strategy):
    def __init__(self):
        self.stoch = bt.ind.StochasticSlow()
    def next(self):
        if not self.position and self.stoch.percK[0] < 20:
            self.buy()
        elif self.stoch.percK[0] > 80:
            self.close()

# Execução
if executar:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

if executar:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

for ativo in ativos:
    st.subheader(f"⏳ Analisando ativo: {ativo}")
    df = yf.download(ativo, start=data_inicio, end=data_fim)

    # Debug: mostrar preview ou erro
    if df is None or df.empty:
        st.warning(f"Nenhum dado retornado para o ativo {ativo}. Verifique o ticker ou o período selecionado.")
        continue
    else:
        st.success(f"✅ Dados carregados para {ativo}.")
        st.dataframe(df.head())

    df.columns = [col.strip() for col in df.columns]
    expected_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    df = df[[col for col in expected_cols if col in df.columns]]

    data = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(10000)
    cerebro.adddata(data)
    cerebro.addstrategy(eval(estrategias[estrategia_nome]))

    class Equity(bt.Analyzer):
        def __init__(self): self.equity = []
        def next(self): self.equity.append(self.strategy.broker.getvalue())

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(Equity, _name='equity')

    results = cerebro.run()[0]
    equity = results.analyzers.equity.equity
    ax.plot(equity, label=ativo)

    resultados.append({
        'Ação': ativo,
        'Retorno Total (R$)': round(equity[-1] - 10000, 2),
        'Sharpe': round(results.analyzers.sharpe.get_analysis().get('sharperatio', 0), 2),
        'Drawdown (%)': round(results.analyzers.drawdown.get_analysis()['max']['drawdown'], 2)
    })

    ax.set_title(f'💰 Curva de Capital - Estratégia: {estrategia_nome}')
    ax.set_xlabel('Período')
    ax.set_ylabel('Valor da Carteira (R$)')
    ax.legend()
    st.pyplot(fig)

    df_resultados = pd.DataFrame(resultados)
    st.markdown("### 📄 Resultados do Backtest")
    st.dataframe(df_resultados)

# 📥 Exportar Relatório em PDF (se disponível)
st.markdown("---")
st.markdown("### 📥 Exportar Relatório")

try:
    with open("relatorio_backtest_b3_final.pdf", "rb") as pdf_file:
        st.download_button(
            label="📄 Baixar PDF com Gráfico e Métricas",
            data=pdf_file,
            file_name="relatorio_backtest_b3_final.pdf",
            mime="application/pdf"
        )
except FileNotFoundError:
    st.info("⚠️ Execute ao menos um backtest para gerar o relatório em PDF.")

# 🌙 Tema escuro pode ser ativado no menu lateral → Settings → Theme → Dark
