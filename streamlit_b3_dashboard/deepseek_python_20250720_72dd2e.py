# Corrected data download and processing section:
if executar and ativos:
    resultados = []
    fig, ax = plt.subplots(figsize=(12, 6))

    for ativo in ativos:
        if not ativo.endswith(".SA"):
            ativo += ".SA"

        try:
            # Download dos dados históricos para métricas agregadas
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
            
            # Seleção das colunas desejadas para o backtest
            df = df[colunas_disponiveis]
            
            if df.empty:
                st.warning(f"⚠️ Dados insuficientes após filtro para {ativo}.")
                continue
                
            data_feed = bt.feeds.PandasData(dataname=df)
            cerebro = bt.Cerebro()
            cerebro.broker.set_cash(10000)
            cerebro.adddata(data_feed)
            
            for estrategia_nome in estrategias_selecionadas:
                if estrategia_nome not in estrategias:
                    st.error(f"Estratégia '{estrategia_nome}' não encontrada no dicionário.")
                    continue
                    
                classe_estrategia = globals()[estrategias[estrategia_nome]]
                cerebro.addstrategy(classe_estrategia)
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
                cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
                cerebro.addanalyzer(Equity, _name='equity')

                # Executa a simulação da estratégia
                results = cerebro.run()[0]
                equity = results.analyzers.equity.equity
                ax.plot(equity, label=f"{ativo} - {estrategia_nome}")

                resultados.append({
                    'Ação': ativo,
                    'Estratégia': estrategia_nome,
                    'Retorno Total (R$)': round(equity[-1] - 10000, 2),
                    'Sharpe': round(results.analyzers.sharpe.get_analysis().get('sharperatio', 0), 2),
                    'Drawdown (%)': round(results.analyzers.drawdown.get_analysis()['max']['drawdown'], 2)
                })

        except Exception as e:
            st.error(f"Erro ao processar o ativo {ativo}: {e}")
            continue

    if resultados:  # Only plot if we have results
        st.pyplot(fig)
        df_result = pd.DataFrame(resultados)
        st.dataframe(df_result)