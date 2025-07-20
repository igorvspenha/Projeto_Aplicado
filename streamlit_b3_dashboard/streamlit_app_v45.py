
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

estrategias_selecionadas = st.multiselect("Escolha até 10 estratégias:", list(estrategias.keys()), max_selections=10)
executar = st.button("🚀 Executar Backtest")

class Equity(bt.Analyzer):
    def __init__(self):
        self.equity = []
    def next(self):
        self.equity.append(self.strategy.broker.getvalue())

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

classe_estrategia = globals()[estrategias[estrategia_nome]]

if executar and ativos:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

    for ativo in ativos:
        if not ativo.endswith(".SA"):
            ativo += ".SA"

        try:
            df = yf.download(ativo, start=data_inicio, end=data_fim)
            if df.empty:
                st.warning(f"⚠️ Nenhum dado encontrado para o ativo {ativo}.")
                continue

            if isinstance(df.columns, pd.MultiIndex):
                st.warning(f"⚠️ Formato inesperado de colunas para {ativo}.")
                continue

            df.columns = [col.strip() for col in df.columns if isinstance(col, str)]
            colunas_esperadas = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            colunas_disponiveis = [col for col in colunas_esperadas if col in df.columns]
if not colunas_disponiveis:
    st.warning(f"⚠️ Formato inesperado de colunas para o ativo {ativo}.")
    continue
df = df[colunas_disponiveis]

            if df.empty:
                st.warning(f"⚠️ Dados insuficientes após filtro para {ativo}.")
                continue

            data_feed = bt.feeds.PandasData(dataname=df)
            cerebro = bt.Cerebro()
            cerebro.broker.set_cash(10000)
            cerebro.adddata(data_feed)
            cerebro.addstrategy(classe_estrategia)
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

        except Exception as e:
            st.error(f"Erro ao processar o ativo {ativo}: {e}")
            continue

    st.pyplot(fig)
    df_result = pd.DataFrame(resultados)
    st.dataframe(df_result)


# -------------------------
# 📥 Exportar Resultados
# -------------------------

import io

# DataFrame para guardar resultados
resultados_lista = []

# Novo loop com coleta de KPIs
for estrategia_nome in estrategias_selecionadas:
    st.subheader(f"🔍 Estratégia: {estrategia_nome}")
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=95)

    classe_estrategia = globals()[estrategias[estrategia_nome]]
    cerebro.addstrategy(classe_estrategia)

    for ticker in ativos:
        dados = yf.download(ticker, start=data_inicio, end=data_fim)
        if not dados.empty:
            dados_bt = bt.feeds.PandasData(dataname=dados)
            cerebro.adddata(dados_bt, name=ticker)

    resultado = cerebro.run()
    valor_final = cerebro.broker.getvalue()
    retorno = (valor_final - 100000) / 100000

    resultados_lista.append({
        "Estratégia": estrategia_nome,
        "Retorno (%)": round(retorno * 100, 2),
        "Valor Final (R$)": round(valor_final, 2),
    })

    st.write(f"Valor final da carteira: R$ {valor_final:,.2f}")
    st.pyplot(cerebro.plot(style='candlestick')[0][0])

# Converter para DataFrame
df_resultados = pd.DataFrame(resultados_lista)

# Filtros adicionais
with st.expander("🔍 Filtros de Desempenho"):
    min_retorno = st.slider("Retorno mínimo (%)", min_value=-100, max_value=500, value=-100)
    df_filtrado = df_resultados[df_resultados["Retorno (%)"] >= min_retorno]

    st.dataframe(df_filtrado)

# Gráfico de barras comparativo
st.subheader("📊 Comparação de Retorno entre Estratégias")
st.bar_chart(df_filtrado.set_index("Estratégia")["Retorno (%)"])

# Botão para download CSV
csv_buffer = io.StringIO()
df_resultados.to_csv(csv_buffer, index=False)
st.download_button(
    label="📥 Baixar resultados em CSV",
    data=csv_buffer.getvalue(),
    file_name="resultados_backtest.csv",
    mime="text/csv"
)
