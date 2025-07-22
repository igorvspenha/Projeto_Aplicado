import yfinance as yf
import pandas as pd


def load_data_with_indicators(ticker: str, start: str, end: str,
                              sma_period: int = 20, ema_period: int = 20) -> pd.DataFrame:
    """Download historical data and compute SMA and EMA indicators.

    Parameters
    ----------
    ticker : str
        Stock ticker recognized by Yahoo Finance (e.g. ``'PETR4.SA'``).
    start : str
        Start date in ``YYYY-MM-DD`` format.
    end : str
        End date in ``YYYY-MM-DD`` format.
    sma_period : int, optional
        Window size for the simple moving average. Default is ``20``.
    ema_period : int, optional
        Window size for the exponential moving average. Default is ``20``.

    Returns
    -------
    pandas.DataFrame
        DataFrame with historical OHLC data plus ``SMA`` and ``EMA`` columns.
    """
    df = yf.download(ticker, start=start, end=end)
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'.")

    # Ensure the index is a DatetimeIndex and sort the data chronologically
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    # Calculate indicators
    df['SMA'] = df['Close'].rolling(window=sma_period).mean()
    df['EMA'] = df['Close'].ewm(span=ema_period, adjust=False).mean()

    return df
