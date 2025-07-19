
import streamlit as st
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import date

# Interface do usuário
st.set_page_config(page_title="Backtesting B3", layout="wide")
st.title("📈 Backtesting de Estratégias Quantitativas com Ações da B3")

ativos = st.multiselect("Escolha até 3 ações:", ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'B3SA3.SA', 'ABEV3.SA'], default=['PETR4.SA'])
estrategia_nome = st.selectbox("Escolha uma estratégia:", [
    "StrategySMA", "StrategyEMACross", "StrategyRSI2", "StrategyBollinger", "StrategyStochasticSlow"
])

data_inicio = st.date_input("Data de início", value=date(2021, 1, 1))
data_fim = st.date_input("Data de fim", value=date.today())
executar = st.button("🚀 Executar Backtest")

# Estratégias
class StrategySMA(bt.Strategy):
    def __init__(self): self.sma = bt.indicators.SimpleMovingAverage(period=20)
    def next(self):
        if not self.position and self.data.close[0] > self.sma[0]: self.buy()
        elif self.position and self.data.close[0] < self.sma[0]: self.close()

class StrategyEMACross(bt.Strategy):
    def __init__(self):
        self.ema1 = bt.ind.EMA(period=10)
        self.ema2 = bt.ind.EMA(period=30)
    def next(self):
        if not self.position and self.ema1[0] > self.ema2[0]: self.buy()
        elif self.position and self.ema1[0] < self.ema2[0]: self.close()

class StrategyRSI2(bt.Strategy):
    def __init__(self): self.rsi = bt.ind.RSI(period=2)
    def next(self):
        if not self.position and self.rsi < 10: self.buy()
        elif self.position and self.rsi > 90: self.close()

class StrategyBollinger(bt.Strategy):
    def __init__(self): self.bb = bt.indicators.BollingerBands()
    def next(self):
        if not self.position and self.data.close[0] < self.bb.lines.bot[0]: self.buy()
        elif self.position and self.data.close[0] > self.bb.lines.top[0]: self.close()

class StrategyStochasticSlow(bt.Strategy):
    def __init__(self): self.stoch = bt.ind.StochasticSlow()
    def next(self):
        if not self.position and self.stoch.percK[0] < 20: self.buy()
        elif self.stoch.percK[0] > 80: self.close()

estrategias = {
    "StrategySMA": StrategySMA,
    "StrategyEMACross": StrategyEMACross,
    "StrategyRSI2": StrategyRSI2,
    "StrategyBollinger": StrategyBollinger,
    "StrategyStochasticSlow": StrategyStochasticSlow
}

# Execução
if executar:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

    for ativo in ativos:
        st.subheader(f"⏳ Analisando ativo: {ativo}")
        df = yf.download(ativo, start=data_inicio, end=data_fim)

        if df is None or df.empty:
            st.warning(f"⚠️ Nenhum dado retornado para o ativo {ativo}. Verifique o ticker ou o período.")
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
        cerebro.addstrategy(estrategias[estrategia_nome])

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

    ax.set_title("Curva de Capital por Ativo")
    ax.legend()
    st.pyplot(fig)

    st.subheader("📊 Resultados Comparativos")
    st.dataframe(resultados)
