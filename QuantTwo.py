# 40% win rate

from AlgorithmImports import *


class EnhancedTradingAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Set backtest period
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 1, 1)

        # Set initial cash
        self.SetCash(100000)

        # Add currency pair to trade (EURUSD in this case)
        self.symbol = self.AddForex("EURUSD", Resolution.Daily).Symbol

        # Indicators: EMA for crossover, ATR for dynamic stop-loss, RSI for confirmation
        self.ema_short = self.EMA(
            self.symbol, 50, Resolution.Daily)  # Short-term EMA
        self.ema_long = self.EMA(
            self.symbol, 200, Resolution.Daily)  # Long-term EMA
        self.rsi = self.RSI(
            self.symbol, 14, MovingAverageType.Wilders, Resolution.Daily)
        # ATR for stop-loss
        self.atr = self.ATR(
            self.symbol, 14, MovingAverageType.Wilders, Resolution.Daily)

        # Track entry price and trade size
        self.entry_price = None
        # Risk 2% of portfolio equity per trade (higher risk to increase rewards)
        self.percent_risk = 0.02

        # Set warm-up to ensure sufficient data for indicators
        self.SetWarmUp(200)

    def OnData(self, data):
        # Ensure warm-up period is over and indicators are ready
        if self.IsWarmingUp:
            return

        if not (self.ema_short.IsReady and self.ema_long.IsReady and self.rsi.IsReady and self.atr.IsReady):
            return

        # Ensure data is available for symbol
        if not data.ContainsKey(self.symbol) or not data[self.symbol]:
            return

        # Trade logic
        holdings = self.Portfolio[self.symbol].Quantity
        current_price = data[self.symbol].Price
        ema_short_value = self.ema_short.Current.Value
        ema_long_value = self.ema_long.Current.Value
        rsi_value = self.rsi.Current.Value
        atr_value = self.atr.Current.Value

        # Calculate position size based on volatility (ATR)
        position_size = self.CalculatePositionSize(atr_value, current_price)

        # Loosen the RSI conditions: Only confirm that it's not extremely overbought/oversold
        # Check for buy signal (50 EMA crossing above 200 EMA and RSI > 40 to loosen conditions)
        if holdings == 0 and ema_short_value > ema_long_value and rsi_value > 40:
            self.MarketOrder(self.symbol, position_size)  # Buy full size
            self.entry_price = current_price
            self.Debug(f"Buy at {self.entry_price}")

        # Check for sell signal (50 EMA crossing below 200 EMA and RSI < 60 to loosen conditions)
        elif holdings == 0 and ema_short_value < ema_long_value and rsi_value < 60:
            self.MarketOrder(self.symbol, -position_size)  # Sell full size
            self.entry_price = current_price
            self.Debug(f"Sell at {self.entry_price}")

        # Exit conditions: Trailing stop (1x ATR) and Profit-Taking (2x ATR)
        if holdings > 0 and current_price < self.entry_price - 1 * atr_value:
            self.Liquidate(self.symbol)
            self.Debug(
                f"Stop-loss hit, closing long position at {current_price}")
        elif holdings > 0 and current_price > self.entry_price + 2 * atr_value:
            self.Liquidate(self.symbol)
            self.Debug(
                f"Take-profit hit, closing long position at {current_price}")

        if holdings < 0 and current_price > self.entry_price + 1 * atr_value:
            self.Liquidate(self.symbol)
            self.Debug(
                f"Stop-loss hit, closing short position at {current_price}")
        elif holdings < 0 and current_price < self.entry_price - 2 * atr_value:
            self.Liquidate(self.symbol)
            self.Debug(
                f"Take-profit hit, closing short position at {current_price}")

    def CalculatePositionSize(self, atr_value, current_price):
        """
        Calculate position size based on portfolio risk (2% risk).
        """
        risk_per_trade = self.Portfolio.Cash * self.percent_risk
        # 1x ATR for stop-loss risk calculation
        position_size = risk_per_trade / (atr_value * 1)
        return min(position_size, self.Portfolio.TotalPortfolioValue / current_price)
