
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import backtrader as bt
import streamlit as st
from datetime import datetime
from io import BytesIO

st.title('Comparação Cruzada de Estratégias e Ações - Ibovespa')

# Lista completa de ações do Ibovespa (simplificada para exemplo)
acoes_ibov = sorted([
    'ABEV3.SA', 'ALPA4.SA', 'AMER3.SA', 'ASAI3.SA', 'AZUL4.SA', 'B3SA3.SA', 'BBAS3.SA',
    'BBDC3.SA', 'BBDC4.SA', 'BBSE3.SA', 'BEEF3.SA', 'BPAC11.SA', 'BRAP4.SA', 'BRFS3.SA',
    'BRKM5.SA', 'BRML3.SA', 'CASH3.SA', 'CCRO3.SA', 'CIEL3.SA', 'CMIG4.SA', 'COGN3.SA',
    'CPFE3.SA', 'CPLE6.SA', 'CRFB3.SA', 'CSAN3.SA', 'CSNA3.SA', 'CVCB3.SA', 'CYRE3.SA',
    'DXCO3.SA', 'ECOR3.SA', 'EGIE3.SA', 'ELET3.SA', 'ELET6.SA', 'EMBR3.SA', 'ENBR3.SA',
    'ENEV3.SA', 'ENGI11.SA', 'EQTL3.SA', 'EZTC3.SA', 'GGBR4.SA', 'GOAU4.SA', 'GOLL4.SA',
    'HAPV3.SA', 'HBOR3.SA', 'HYPE3.SA', 'IGTI11.SA', 'IRBR3.SA', 'ITSA4.SA', 'ITUB4.SA',
    'JBSS3.SA', 'KLBN11.SA', 'LREN3.SA', 'LWSA3.SA', 'MGLU3.SA', 'MRFG3.SA', 'MRVE3.SA',
    'MULT3.SA', 'NTCO3.SA', 'PETR3.SA', 'PETR4.SA', 'PRIO3.SA', 'QUAL3.SA', 'RADL3.SA',
    'RAIL3.SA', 'RDOR3.SA', 'RENT3.SA', 'RRRP3.SA', 'SANB11.SA', 'SBSP3.SA', 'SLCE3.SA',
    'SMTO3.SA', 'SULA11.SA', 'SUZB3.SA', 'TAEE11.SA', 'TIMS3.SA', 'TOTS3.SA', 'UGPA3.SA',
    'USIM5.SA', 'VALE3.SA', 'VIVT3.SA', 'WEGE3.SA', 'YDUQ3.SA'
])

# Entrada do usuário
ativos = st.multiselect('Escolha até 3 ações para comparar:', acoes_ibov, default=['PETR4.SA', 'VALE3.SA', 'ITUB4.SA'])
estrategias = st.multiselect('Escolha as estratégias a aplicar:', ['Strategy1', 'Strategy2', 'Strategy3', 'Strategy4', 'Strategy5'], default=['Strategy1', 'Strategy3'])
data_inicio = st.date_input('Data de Início:', datetime(2018, 1, 1))
data_fim = st.date_input('Data de Fim:', datetime(2024, 12, 31))

# Parâmetros padrão
params = {
    'Strategy1': {'fast': 10, 'slow': 30, 'vol_window': 20, 'vol_threshold': 0.02},
    'Strategy5': {'momentum_period': 15, 'stop_loss': 0.05, 'take_profit': 0.10}
}

# Estratégias
class Strategy1(bt.Strategy):
    params = (('fast', 10), ('slow', 30), ('vol_window', 20), ('vol_threshold', 0.02))
    def __init__(self):
        self.ma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.fast)
        self.ma_slow = bt.indicators.SimpleMovingAverage(self.data.close, period=self.p.slow)
        self.returns = bt.indicators.PercentChange(self.data.close)
        self.volatility = bt.indicators.StandardDeviation(self.returns, period=self.p.vol_window)
    def next(self):
        if not self.position and self.ma_fast[0] > self.ma_slow[0] and self.volatility[0] > self.p.vol_threshold:
            self.buy()
        elif self.ma_fast[0] < self.ma_slow[0]:
            self.close()

class Strategy2(bt.Strategy):
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        self.macd = bt.indicators.MACD(self.data.close)
    def next(self):
        if not self.position and self.rsi[0] < 30 and self.macd.macd[0] > self.macd.signal[0]:
            self.buy()
        elif self.rsi[0] > 70:
            self.close()

class Strategy3(bt.Strategy):
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(self.data.close, period=20)
        self.vol_avg = bt.indicators.SimpleMovingAverage(self.data.volume, period=20)
    def next(self):
        if not self.position and self.data.close[0] < self.bb.lines.bot[0] and self.data.volume[0] > self.vol_avg[0]:
            self.buy()
        elif self.data.close[0] > self.bb.lines.mid[0]:
            self.close()

class Strategy4(bt.Strategy):
    def __init__(self):
        self.ema = bt.ind.EMA(self.data.close, period=20)
        self.std = bt.ind.StandardDeviation(self.data.close, period=20)
    def next(self):
        z = (self.data.close[0] - self.ema[0]) / self.std[0]
        if not self.position and z < -2:
            self.buy()
        elif z > 0:
            self.close()

class Strategy5(bt.Strategy):
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

# Executar comparações cruzadas
resultados = []
plt.figure(figsize=(12, 6))
for ativo in ativos:
    df = yf.download(ativo, start=data_inicio, end=data_fim)
    df.to_csv(f'{ativo}.csv')
    for estrategia in estrategias:
        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(10000)
        data = bt.feeds.YahooFinanceCSVData(dataname=f'{ativo}.csv')
        cerebro.adddata(data)
        if estrategia == 'Strategy1':
            cerebro.addstrategy(Strategy1, **params['Strategy1'])
        elif estrategia == 'Strategy5':
            cerebro.addstrategy(Strategy5, **params['Strategy5'])
        else:
            cerebro.addstrategy(eval(estrategia))

        class Equity(bt.Analyzer):
            def __init__(self): self.equity = []
            def next(self): self.equity.append(self.strategy.broker.getvalue())

        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(Equity, _name='equity')

        results = cerebro.run()[0]
        equity = results.analyzers.equity.equity
        plt.plot(equity, label=f'{ativo}-{estrategia}')

        resultados.append({
            'Ação': ativo,
            'Estratégia': estrategia,
            'Retorno Total (R$)': equity[-1] - 10000,
            'Sharpe': results.analyzers.sharpe.get_analysis().get('sharperatio', 0),
            'Drawdown (%)': results.analyzers.drawdown.get_analysis()['max']['drawdown']
        })

plt.title('Curvas de Capital - Estratégias e Ações')
plt.xlabel('Período')
plt.ylabel('Valor da Carteira (R$)')
plt.legend()
st.pyplot()

df_resultados = pd.DataFrame(resultados)
st.dataframe(df_resultados)

# Exportar Excel
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_resultados.to_excel(writer, index=False, sheet_name='Resultados')
    writer.save()
st.download_button(label='📥 Baixar Resultados em Excel', data=output.getvalue(), file_name='comparacao_cruzada.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
