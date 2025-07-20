import streamlit as st
import yfinance as yf
import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Backtesting B3", layout="wide")
st.title("📈 Backtesting de Estratégias Quantitativas - B3")

TICKERS_B3 = sorted([
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA",
    "WEGE3.SA", "BBAS3.SA", "RENT3.SA", "MGLU3.SA", "ELET3.SA",
    "B3SA3.SA", "CSNA3.SA", "SUZB3.SA", "PRIO3.SA", "RAIZ4.SA",
    "GGBR4.SA", "KLBN11.SA", "LREN3.SA", "BRFS3.SA", "EMBR3.SA"
])

ativos = st.multiselect("Selecione até 3 ativos da B3:", TICKERS_B3, max_selections=3)

col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data inicial", value=date(2022, 1, 1))
with col2:
    data_fim = st.date_input("Data final", value=date.today())

estrategias = {
    "Stochastic Oscillator": "StrategyStochasticSlow",
    "Cruzamento de Médias Simples": "StrategySMACross",
    "Cruzamento de Médias Exponenciais": "StrategyEMACross",
    "Bandas de Bollinger": "StrategyBollinger",
    "Índice de Força Relativa (RSI)": "StrategyRSI",
    "MACD": "StrategyMACD",
    "ADX + DI": "StrategyADX",
    "Momentum": "StrategyMomentum",
    "Ichimoku Kinko Hyo": "StrategyIchimoku",
    "Moving Average & RSI": "StrategyMARSI"
}

estrategia_nome = st.selectbox("Escolha a estratégia para backtest:", list(estrategias.keys()))
executar = st.button("🚀 Executar Backtest")

class StrategyStochasticSlow(bt.Strategy):
    def __init__(self):
        self.stoch = bt.ind.StochasticSlow()
    def next(self):
        if not self.position and self.stoch.percK[0] < 20:
            self.buy()
        elif self.stoch.percK[0] > 80:
            self.close()




class StrategySMACross(bt.Strategy):
    params = (("fast", 10), ("slow", 30),)

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.params.fast)
        sma2 = bt.ind.SMA(period=self.params.slow)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.close()

class StrategyEMACross(bt.Strategy):
    def __init__(self):
        ema1 = bt.ind.EMA(period=12)
        ema2 = bt.ind.EMA(period=26)
        self.crossover = bt.ind.CrossOver(ema1, ema2)

    def next(self):
        if not self.position and self.crossover > 0:
            self.buy()
        elif self.position and self.crossover < 0:
            self.close()

class StrategyBollinger(bt.Strategy):
    def __init__(self):
        self.bb = bt.ind.BollingerBands()

    def next(self):
        if not self.position and self.data.close[0] < self.bb.lines.bot[0]:
            self.buy()
        elif self.position and self.data.close[0] > self.bb.lines.top[0]:
            self.close()

class StrategyRSI(bt.Strategy):
    def __init__(self):
        self.rsi = bt.ind.RSI(period=14)

    def next(self):
        if not self.position and self.rsi < 30:
            self.buy()
        elif self.position and self.rsi > 70:
            self.close()

class StrategyMACD(bt.Strategy):
    def __init__(self):
        self.macd = bt.ind.MACD()

    def next(self):
        if not self.position and self.macd.macd[0] > self.macd.signal[0]:
            self.buy()
        elif self.position and self.macd.macd[0] < self.macd.signal[0]:
            self.close()

class StrategyADX(bt.Strategy):
    def __init__(self):
        self.adx = bt.ind.ADX()

    def next(self):
        if not self.position and self.adx > 25:
            self.buy()
        elif self.position and self.adx < 20:
            self.close()

class StrategyMomentum(bt.Strategy):
    def __init__(self):
        self.mom = bt.ind.Momentum(period=10)

    def next(self):
        if not self.position and self.mom > 0:
            self.buy()
        elif self.position and self.mom < 0:
            self.close()

class StrategyIchimoku(bt.Strategy):
    def __init__(self):
        self.ichi = bt.ind.Ichimoku()

    def next(self):
        if not self.position and self.data.close[0] > self.ichi.senkou_span_a[0]:
            self.buy()
        elif self.position and self.data.close[0] < self.ichi.senkou_span_b[0]:
            self.close()

class StrategyMARSI(bt.Strategy):
    def __init__(self):
        self.sma = bt.ind.SMA(period=14)
        self.rsi = bt.ind.RSI(period=14)

    def next(self):
        if not self.position and self.data.close[0] > self.sma and self.rsi < 30:
            self.buy()
        elif self.position and self.rsi > 70:
            self.close()


if executar and ativos:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

    for ativo in ativos:

    if not ativo.endswith(".SA"):
        ativo += ".SA"  # força padrão do Yahoo Finance para ativos da B3

    df = yf.download(ativo, start=data_inicio, end=data_fim)

    if df is None or df.empty:
        st.warning(f"⚠️ Nenhum dado encontrado para o ativo {ativo}. Verifique o ticker ou o período.")
        continue

    if not isinstance(df, pd.DataFrame) or not isinstance(df.columns, pd.Index):
        st.error(f"❌ Formato inesperado para o ativo {ativo}: tipo de colunas inválido.")
        st.write(df)
        continue

    try:
        df.columns = [col.strip() for col in df.columns if isinstance(col, str)]
    except Exception as e:
        st.error(f"Erro ao processar colunas do ativo {ativo}: {e}")
        st.write(df)
        continue

    expected_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    df = df[[col for col in expected_cols if col in df.columns]]

    if df.empty or len(df.columns) == 0:
        st.warning(f"⚠️ Dados insuficientes após filtro para o ativo {ativo}.")
        continue

    st.success(f"✅ Dados carregados com sucesso para {ativo}")
    st.dataframe(df.head())

    data = bt.feeds.PandasData(dataname=df)




        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(10000)
        cerebro.adddata(data)
        cerebro.addstrategy(StrategyStochasticSlow)

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

    st.pyplot(fig)
    df_result = pd.DataFrame(resultados)
    st.dataframe(df_result)