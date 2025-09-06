import pandas as pd
import math


class Portfolio:
    """Simple portfolio accounting.

    - initial_cash: starting capital
    - position_size: fraction of current equity to use when entering a trade (0-1)
    """

    def __init__(self, initial_cash: float = 10000.0, position_size: float = 0.1, transaction_cost_per_share: float = 0.0, slippage_per_share: float = 0.0):
        """transaction_cost_per_share and slippage_per_share are in absolute currency units per share."""
        assert 0 < position_size <= 1.0
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.position = 0  # number of shares
        self.position_avg_price = 0.0
        self.position_size = position_size
        self.transaction_cost_per_share = float(transaction_cost_per_share)
        self.slippage_per_share = float(slippage_per_share)
        self.history = []

    def enter_long(self, price: float, time):
        # invest fraction of current equity
        equity = self.current_equity(price)
        invest = equity * self.position_size
        if invest < price:
            return  # can't buy even one share
        qty = math.floor(invest / price)
        # account for slippage and transaction costs
        per_share_cost = price + self.slippage_per_share + self.transaction_cost_per_share
        cost = qty * per_share_cost
        self.cash -= cost
        # update weighted average price if adding to position
        if self.position == 0:
            self.position_avg_price = price
        else:
            self.position_avg_price = (
                self.position_avg_price * self.position + price * qty
            ) / (self.position + qty)
        self.position += qty
        self.history.append({"time": time, "action": "buy", "price": price, "qty": qty, "cost": cost, "per_share_cost": per_share_cost})

    def exit_long(self, price: float, time):
        if self.position == 0:
            return
        per_share_proceeds = price - (self.slippage_per_share + self.transaction_cost_per_share)
        proceeds = self.position * per_share_proceeds
        self.cash += proceeds
        self.history.append({"time": time, "action": "sell", "price": price, "qty": self.position, "proceeds": proceeds, "per_share_proceeds": per_share_proceeds})
        self.position = 0
        self.position_avg_price = 0.0

    def current_equity(self, price: float) -> float:
        return self.cash + self.position * price

    def record(self, time, price):
        self.history.append({"time": time, "action": "mark", "price": price, "qty": self.position, "cash": self.cash, "equity": self.current_equity(price)})

    def trades_df(self) -> pd.DataFrame:
        return pd.DataFrame([h for h in self.history if h.get("action") in ("buy", "sell")])

    def equity_series(self) -> pd.DataFrame:
        df = pd.DataFrame(self.history)
        if df.empty:
            return pd.DataFrame()
        df = df[df['action'] == 'mark'][['time', 'equity']]
        df = df.set_index('time').sort_index()
        return df
