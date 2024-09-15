import pandas as pd
import numpy as np
import plotly.graph_objects as go
import vectorbt as vbt


class SOLUSDTBreakoutStrategy:
    def __init__(self, data, window_size=14):
        self.data = data
        self.window_size = window_size
        self.supports = None
        self.resistances = None
        self.portfolio = None

    def detect_pivots(self):
        """
        Detect support (lows) and resistance (highs) levels over a rolling window.
        """
        high = self.data['high']
        low = self.data['low']

        # Resistance (High Pivot) - look for maximum highs in the window
        resistances = high.rolling(window=self.window_size).max()

        # Support (Low Pivot) - look for minimum lows in the window
        supports = low.rolling(window=self.window_size).min()

        # Backfill NA values (start of series)
        self.supports = supports.bfill()  # Use .bfill() to replace deprecated method
        self.resistances = resistances.bfill()

        return self.supports, self.resistances

    def plot_with_pivots_and_signals(self, entries, exits):
        """
        Plot the candlestick chart along with detected support/resistance pivots and entry/exit signals.
        """
        # Create candlestick chart with Plotly
        fig = go.Figure(data=[go.Candlestick(x=self.data.index,
                                             open=self.data['open'],
                                             high=self.data['high'],
                                             low=self.data['low'],
                                             close=self.data['close'],
                                             name='Price')])

        # Add support and resistance levels
        fig.add_trace(go.Scatter(x=self.data.index, y=self.resistances,
                                 mode='lines', line=dict(color='red', width=1),
                                 name='Resistance (High)'))
        fig.add_trace(go.Scatter(x=self.data.index, y=self.supports,
                                 mode='lines', line=dict(color='green', width=1),
                                 name='Support (Low)'))

        # Add buy signals
        fig.add_trace(go.Scatter(x=self.data.index[entries],
                                 y=self.data['close'][entries],
                                 mode='markers',
                                 marker=dict(symbol='triangle-up',
                                             color='blue', size=10),
                                 name='Buy Signal'))

        # Add sell signals
        fig.add_trace(go.Scatter(x=self.data.index[exits],
                                 y=self.data['close'][exits],
                                 mode='markers',
                                 marker=dict(symbol='triangle-down',
                                             color='red', size=10),
                                 name='Sell Signal'))

        # Customize layout
        fig.update_layout(title='SOL/USDT Candlestick Chart with Breakout Pivots and Signals',
                          yaxis_title='Price',
                          xaxis_title='Time',
                          template='plotly_dark')

        # Display the chart
        fig.show()

    def backtest(self, fee=0.001):
        """
        Backtest the strategy using support/resistance breakouts. Assumes transaction fees.
        Buy when price exceeds resistance, sell when price falls below support.
        """
        # Entry signals: Close price breaking above resistance
        entries = self.data['close'] > self.resistances.shift(1)

        # Exit signals: Close price falling below support
        exits = self.data['close'] < self.supports.shift(1)

        # Apply the backtest using vectorbt with frequency set to 1h
        self.portfolio = vbt.Portfolio.from_signals(
            self.data['close'], entries, exits, fees=fee, freq='1h')
        return self.portfolio, entries, exits

    def log_backtest_results(self):
        """
        Log and save the backtest results to CSV.
        """
        result_summary = self.portfolio.stats()
        print(result_summary)
        result_summary.to_csv('sol_usdt_backtest_results.csv')
        return result_summary

    def run_strategy(self):
        """
        Run the entire strategy: detect pivots, backtest, and plot results.
        """
        self.detect_pivots()
        portfolio, entries, exits = self.backtest()
        self.plot_with_pivots_and_signals(entries, exits)
        self.log_backtest_results()


# Read SOL/USDT data from CSV file
data = pd.read_csv('sol_usdt_5y_kline_data.csv', parse_dates=[
                   'Gmt time'], index_col='Gmt time')

# Ensure column names are in lowercase for easier access
data.columns = data.columns.str.lower()

# Initialize and run the breakout strategy
sol_usdt_strategy = SOLUSDTBreakoutStrategy(data, window_size=14)
sol_usdt_strategy.run_strategy()
