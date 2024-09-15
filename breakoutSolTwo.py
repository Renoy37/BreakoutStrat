import pandas as pd
import plotly.graph_objs as go
import numpy as np

# Load your data from CSV (SOL/USDT 5-year data)
data = pd.read_csv('sol_usdt_5y_kline_data.csv')

# Convert 'Gmt time' to datetime for easier plotting
data['Gmt time'] = pd.to_datetime(data['Gmt time'])

# Calculate Pivots (Highs and Lows)


def calculate_pivots(data, window_size=5):
    pivots_high = data['high'].rolling(window=window_size, center=True).max()
    pivots_low = data['low'].rolling(window=window_size, center=True).min()
    return pivots_high, pivots_low


# Get pivot points for breakout zones
pivots_high, pivots_low = calculate_pivots(data)

# Define buy and sell signals - filtering out noise by considering only significant moves


# Reduced threshold to be more sensitive
def generate_signals(data, pivots_high, pivots_low, threshold=0.005):
    buy_signals = []
    sell_signals = []

    in_position = False  # Track if we're currently holding a position

    for i in range(1, len(data)):
        # Buy: If current price breaks above pivot high and we're not in a position
        if data['close'][i] > pivots_high[i] * (1 + threshold) and not in_position:
            print(f"Buy signal detected at {data['Gmt time'][i]}, price: {
                  data['close'][i]} > pivot high: {pivots_high[i]}")  # Debugging
            buy_signals.append(data['Gmt time'][i])
            in_position = True
        # Sell: If current price breaks below pivot low and we're in a position
        elif data['close'][i] < pivots_low[i] * (1 - threshold) and in_position:
            print(f"Sell signal detected at {data['Gmt time'][i]}, price: {
                  data['close'][i]} < pivot low: {pivots_low[i]}")  # Debugging
            sell_signals.append(data['Gmt time'][i])
            in_position = False

    print(f"Total Buy Signals: {len(buy_signals)}, Total Sell Signals: {
          len(sell_signals)}")  # Debugging
    return buy_signals, sell_signals


# Generate signals (with reduced threshold for more frequent signals)
buy_signals, sell_signals = generate_signals(data, pivots_high, pivots_low)

# Backtest strategy: Calculate profit/loss from buy/sell signals


def backtest_strategy(data, buy_signals, sell_signals):
    position_size = 1  # Assuming we buy and sell 1 unit of SOL for each trade
    trades = []

    # Make sure we have both buy and sell signals and they are synchronized
    min_trades = min(len(buy_signals), len(sell_signals))

    if min_trades == 0:
        print("No trades detected!")
        return [], 0, 0

    for i in range(min_trades):
        buy_time = buy_signals[i]
        sell_time = sell_signals[i]

        # Get buy and sell prices
        buy_price = data.loc[data['Gmt time'] == buy_time, 'close'].values[0]
        sell_price = data.loc[data['Gmt time'] == sell_time, 'close'].values[0]

        # Calculate profit for the trade
        profit = (sell_price - buy_price) * position_size

        # Log trade details
        trades.append({
            'Buy Time': buy_time,
            'Sell Time': sell_time,
            'Buy Price': buy_price,
            'Sell Price': sell_price,
            'Profit': profit  # Ensure 'Profit' is logged correctly
        })

    # Convert trades to DataFrame
    trades_df = pd.DataFrame(trades)

    # Log the results in the console instead of saving them
    print("Trades executed:")
    print(trades_df)

    # Calculate total profit from all trades
    total_profit = trades_df['Profit'].sum() if not trades_df.empty else 0
    num_trades = len(trades_df)

    return trades_df, total_profit, num_trades


# Run the backtest and log the results to console
trades_df, total_profit, num_trades = backtest_strategy(
    data, buy_signals, sell_signals)

# Print out backtest summary
print(f"\nBacktest Summary:")
print(f"Total Profit: {total_profit}")
print(f"Number of Trades: {num_trades}")

# Create the candlestick chart
candlestick = go.Candlestick(
    x=data['Gmt time'],
    open=data['open'],
    high=data['high'],
    low=data['low'],
    close=data['close'],
    name='Price'
)

# Create traces for pivots
pivots_high_trace = go.Scatter(
    x=data['Gmt time'],
    y=pivots_high,
    mode='markers',
    marker=dict(color='purple', size=5),
    name='Resistance (High)'
)

pivots_low_trace = go.Scatter(
    x=data['Gmt time'],
    y=pivots_low,
    mode='markers',
    marker=dict(color='green', size=5),
    name='Support (Low)'
)

# Create buy and sell signal markers
buy_signals_trace = go.Scatter(
    x=buy_signals,
    y=[data.loc[data['Gmt time'] == signal, 'close'].values[0]
        for signal in buy_signals],
    mode='markers',
    marker=dict(color='blue', symbol='triangle-up', size=10),
    name='Buy Signal'
)

sell_signals_trace = go.Scatter(
    x=sell_signals,
    y=[data.loc[data['Gmt time'] == signal, 'close'].values[0]
        for signal in sell_signals],
    mode='markers',
    marker=dict(color='red', symbol='triangle-down', size=10),
    name='Sell Signal'
)

# Assemble the layout for better visibility
layout = go.Layout(
    title='SOL/USDT Candlestick Chart with Breakout Pivots and Signals',
    xaxis_title='Time',
    yaxis_title='Price',
    plot_bgcolor='black',
    paper_bgcolor='black',
    font=dict(color='white'),
    xaxis=dict(type='date'),
    yaxis=dict(showgrid=True, gridcolor='gray')
)

# Create the figure
fig = go.Figure(data=[candlestick, pivots_high_trace, pivots_low_trace,
                buy_signals_trace, sell_signals_trace], layout=layout)

# Show the plot
fig.show()
