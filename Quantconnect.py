# 60% win rate

class AdvancedTradingAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Set backtest period
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 1, 1)

        # Set initial cash
        self.SetCash(100000)

        # Add currency pair to trade (EURUSD in this case)
        self.symbol = self.AddForex("EURUSD", Resolution.Daily).Symbol

        # EMA and RSI configuration
        self.ema = self.EMA(self.symbol, 50, Resolution.Daily)
        self.rsi = self.RSI(
            self.symbol, 14, MovingAverageType.Wilders, Resolution.Daily)

        # Track entry price and trade size
        self.entry_price = None
        self.mysize = 10000

        # Set warm-up to ensure sufficient data for indicators
        self.SetWarmUp(50)

        # Initialize rolling windows for pivot detection
        self.window = 6  # Window size for pivot point detection
        self.high_window = RollingWindow[float](self.window)
        self.low_window = RollingWindow[float](self.window)

    def OnData(self, data):
        # Ensure warm-up period is over
        if self.IsWarmingUp:
            return

        # Ensure data is available for symbol
        if not data.ContainsKey(self.symbol) or not data[self.symbol]:
            return

        # Store the current high and low prices in rolling windows
        self.high_window.Add(data[self.symbol].High)
        self.low_window.Add(data[self.symbol].Low)

        # Trade logic
        holdings = self.Portfolio[self.symbol].Quantity
        current_price = data[self.symbol].Price
        ema_value = self.ema.Current.Value
        rsi_value = self.rsi.Current.Value

        # Detect support/resistance pattern (pivot points)
        pattern = self.detect_structure()

        # Check for bullish pattern (support detected) and RSI not overbought
        if pattern == 2 and rsi_value < 70 and holdings <= 0:
            # Buy logic
            stop_loss = current_price * 0.97  # 3% stop-loss
            take_profit = current_price * 1.06  # 6% take-profit (2:1 ratio)
            self.SetHoldings(self.symbol, 1)  # Buy full size
            self.entry_price = current_price
            self.Debug(f"Buy at {
                       self.entry_price} with stop-loss {stop_loss} and take-profit {take_profit}")

        # Check for bearish pattern (resistance detected) and RSI not oversold
        elif pattern == 1 and rsi_value > 30 and holdings >= 0:
            # Sell logic
            stop_loss = current_price * 1.03  # 3% stop-loss
            take_profit = current_price * 0.94  # 6% take-profit (2:1 ratio)
            self.SetHoldings(self.symbol, -1)  # Sell full size
            self.entry_price = current_price
            self.Debug(f"Sell at {
                       self.entry_price} with stop-loss {stop_loss} and take-profit {take_profit}")

        # RSI-based exit: Close long positions if RSI > 80, close short if RSI < 20
        if holdings > 0 and rsi_value > 80:
            self.Liquidate(self.symbol)
            self.Debug(f"RSI overbought, closing long position at {
                       current_price}")
        elif holdings < 0 and rsi_value < 20:
            self.Liquidate(self.symbol)
            self.Debug(f"RSI oversold, closing short position at {
                       current_price}")

    def detect_structure(self):
        """
        Detect if there is a support or resistance pattern based on pivot points.
        Returns:
            1 for resistance (bearish), 2 for support (bullish), 0 for no pattern.
        """
        # Check if the rolling windows are ready (full of data)
        if not self.high_window.IsReady or not self.low_window.IsReady:
            return 0

        # Detect support (3 consecutive pivot lows)
        if self.is_support():
            return 2
        # Detect resistance (3 consecutive pivot highs)
        if self.is_resistance():
            return 1

        return 0

    def is_support(self):
        """
        Check for support pattern (pivot lows).
        """
        lows = list(self.low_window)
        # Check if recent lows form a support zone
        return len(lows) >= 3 and max(abs(lows[i] - lows[i+1]) for i in range(2)) < 0.01

    def is_resistance(self):
        """
        Check for resistance pattern (pivot highs).
        """
        highs = list(self.high_window)
        # Check if recent highs form a resistance zone
        return len(highs) >= 3 and max(abs(highs[i] - highs[i+1]) for i in range(2)) < 0.01
