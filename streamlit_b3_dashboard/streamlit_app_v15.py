# Código simplificado com a linha corrigida
import streamlit as st
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
import pandas as pd

# Simulação de configuração
executar = True
ativos = ['PETR4.SA']
estrategia_nome = 'StrategyStochasticSlow'
data_inicio = '2022-01-01'
data_fim = '2023-01-01'
estrategias = {
    'StrategyStochasticSlow': bt.Strategy
}

class StrategyStochasticSlow(bt.Strategy):
    def __init__(self):
        self.stoch = bt.ind.StochasticSlow()
    def next(self):
        if not self.position and self.stoch.percK[0] < 20:
            self.buy()
        elif self.stoch.percK[0] > 80:
            self.close()

if executar:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

    for ativo in ativos:
        df = yf.download(ativo, start=data_inicio, end=data_fim)

        if df is None or df.empty:
            st.warning(f"⚠️ Nenhum dado retornado para o ativo {ativo}. Verifique o ticker ou o período.")
            continue
        else:
            st.success(f"✅ Dados carregados para {ativo}.")
            st.dataframe(df.head())

            if df is None or df.empty:
            st.warning(f"⚠️ Nenhum dado encontrado para o ativo {ativo}. Verifique o ticker ou o período.")
            continue
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