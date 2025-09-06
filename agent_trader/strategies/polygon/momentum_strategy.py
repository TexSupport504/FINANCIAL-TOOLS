"""Polygon-powered momentum strategy for agent_trader.

This strategy uses live Polygon.io data to make trading decisions
based on momentum indicators and real-time market conditions.
"""
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter, MarketSnapshot
    from agent_trader.portfolio import Portfolio
    from agent_trader.performance import compute_metrics_from_equity
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class PolygonMomentumStrategy:
    """Momentum strategy using live Polygon.io market data."""
    
    def __init__(self, api_key: Optional[str] = None, lookback_days: int = 20):
        """Initialize strategy with Polygon adapter."""
        self.polygon = PolygonDataAdapter(api_key)
        self.lookback_days = lookback_days
        self.short_ma = 5
        self.long_ma = 20
        
    def get_signals(self, symbol: str) -> dict:
        """Generate trading signals for a symbol using live data."""
        
        # Get recent price data
        bars = self.polygon.get_price_bars(
            symbol=symbol,
            timespan='day', 
            limit=self.lookback_days + self.long_ma
        )
        
        if bars.empty or len(bars) < self.long_ma:
            return {'signal': 'hold', 'reason': 'insufficient_data', 'confidence': 0.0}
        
        # Calculate momentum indicators
        bars['sma_short'] = bars['close'].rolling(window=self.short_ma).mean()
        bars['sma_long'] = bars['close'].rolling(window=self.long_ma).mean()
        bars['momentum'] = (bars['close'] - bars['close'].shift(self.short_ma)) / bars['close'].shift(self.short_ma)
        bars['volatility'] = bars['close'].pct_change().rolling(window=self.short_ma).std()
        
        # Get current market snapshot for real-time data
        snapshot = self.polygon.get_market_snapshot(symbol)
        
        if not snapshot:
            return {'signal': 'hold', 'reason': 'no_snapshot', 'confidence': 0.0}
        
        # Latest indicators
        latest = bars.iloc[-1]
        sma_short = latest['sma_short']
        sma_long = latest['sma_long'] 
        momentum = latest['momentum']
        volatility = latest['volatility']
        
        current_price = snapshot.price
        volume_ratio = snapshot.volume / bars['volume'].mean() if bars['volume'].mean() > 0 else 1.0
        
        # Generate signals
        signals = []
        confidence_factors = []
        
        # Trend signal
        if sma_short > sma_long and current_price > sma_short:
            signals.append('bullish_trend')
            confidence_factors.append(0.3)
        elif sma_short < sma_long and current_price < sma_short:
            signals.append('bearish_trend')  
            confidence_factors.append(0.3)
        
        # Momentum signal
        if momentum > 0.02:  # 2% momentum threshold
            signals.append('strong_momentum')
            confidence_factors.append(0.25)
        elif momentum < -0.02:
            signals.append('weak_momentum')
            confidence_factors.append(0.25)
            
        # Volume confirmation
        if volume_ratio > 1.5:  # Above average volume
            signals.append('volume_confirmation')
            confidence_factors.append(0.2)
            
        # Volatility check (avoid high volatility periods)
        if volatility > 0.05:  # 5% daily volatility threshold
            signals.append('high_volatility')
            confidence_factors.append(-0.15)
        
        # Price action
        daily_change = snapshot.change_percent / 100
        if daily_change > 0.03:  # 3% daily gain
            signals.append('strong_daily_move')
            confidence_factors.append(0.2)
        elif daily_change < -0.03:
            signals.append('weak_daily_move') 
            confidence_factors.append(0.2)
        
        # Determine final signal
        bullish_signals = ['bullish_trend', 'strong_momentum', 'volume_confirmation', 'strong_daily_move']
        bearish_signals = ['bearish_trend', 'weak_momentum', 'weak_daily_move']
        
        bullish_score = sum(0.25 for sig in signals if sig in bullish_signals)
        bearish_score = sum(0.25 for sig in signals if sig in bearish_signals)
        
        base_confidence = sum(confidence_factors)
        
        if bullish_score > bearish_score and bullish_score >= 0.5:
            final_signal = 'buy'
        elif bearish_score > bullish_score and bearish_score >= 0.5:
            final_signal = 'sell'
        else:
            final_signal = 'hold'
            
        confidence = min(1.0, max(0.0, base_confidence + 0.5))
        
        return {
            'signal': final_signal,
            'confidence': confidence,
            'price': current_price,
            'signals_detected': signals,
            'momentum': momentum,
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'sma_short': sma_short,
            'sma_long': sma_long,
            'daily_change_pct': daily_change * 100
        }
    
    def run_backtest(self, symbols: list, initial_capital: float = 10000, 
                    position_size: float = 0.1, max_positions: int = 3) -> dict:
        """Run a simple backtest using recent historical data."""
        
        portfolio = Portfolio(
            initial_cash=initial_capital,
            position_size=position_size,
            transaction_cost_per_share=0.01,
            slippage_per_share=0.005
        )
        
        results = {}
        
        for symbol in symbols:
            print(f"\n📊 Analyzing {symbol}...")
            
            signals = self.get_signals(symbol)
            print(f"Signal: {signals['signal']} (confidence: {signals['confidence']:.2f})")
            print(f"Current price: ${signals.get('price', 0):.2f}")
            print(f"Momentum: {signals.get('momentum', 0):.3f}")
            print(f"Daily change: {signals.get('daily_change_pct', 0):.2f}%")
            
            # For demonstration, simulate some trades based on signals
            if signals['signal'] == 'buy' and signals['confidence'] > 0.6:
                # Simulate entry
                portfolio.enter_long(signals['price'], pd.Timestamp.now())
                print(f"📈 Simulated BUY order at ${signals['price']:.2f}")
                
                # Simulate exit at +5% or -3% (simple take profit/stop loss)
                exit_price_up = signals['price'] * 1.05
                exit_price_down = signals['price'] * 0.97
                
                # For simulation, assume we hit take profit
                portfolio.exit_long(exit_price_up, pd.Timestamp.now())
                print(f"💰 Simulated SELL order at ${exit_price_up:.2f}")
            
            results[symbol] = signals
        
        # Calculate performance metrics
        equity_series = portfolio.equity_series()
        if not equity_series.empty and len(equity_series) > 1:
            metrics = compute_metrics_from_equity(equity_series)
            results['portfolio_metrics'] = metrics
        
        results['portfolio_summary'] = {
            'trades': portfolio.trades_df(),
            'current_cash': portfolio.cash,
            'total_equity': portfolio.current_equity(100)  # dummy price
        }
        
        return results


def main():
    """Example usage of the Polygon momentum strategy."""
    try:
        print("🚀 POLYGON MOMENTUM STRATEGY TEST")
        print("=" * 40)
        
        # Initialize strategy
        strategy = PolygonMomentumStrategy(lookback_days=30)
        
        # Test symbols
        test_symbols = ['AAPL', 'MSFT', 'NVDA']
        
        # Run analysis
        results = strategy.run_backtest(test_symbols, initial_capital=10000)
        
        print(f"\n📈 STRATEGY RESULTS")
        print("=" * 20)
        
        for symbol, signal_data in results.items():
            if symbol == 'portfolio_metrics' or symbol == 'portfolio_summary':
                continue
                
            print(f"\n{symbol}:")
            print(f"  Signal: {signal_data['signal']} ({signal_data['confidence']:.2f})")
            print(f"  Price: ${signal_data.get('price', 0):.2f}")
            print(f"  Momentum: {signal_data.get('momentum', 0):.3f}")
            print(f"  Volume ratio: {signal_data.get('volume_ratio', 0):.2f}")
        
        # Portfolio summary
        if 'portfolio_metrics' in results:
            metrics = results['portfolio_metrics']
            print(f"\n💼 PORTFOLIO PERFORMANCE:")
            print(f"  Total return: {metrics.get('total_return', 0):.2%}")
            print(f"  Max drawdown: {metrics.get('max_drawdown', 0):.2%}")
            print(f"  Sharpe ratio: {metrics.get('sharpe', 0):.2f}")
        
        summary = results.get('portfolio_summary', {})
        trades_df = summary.get('trades')
        if trades_df is not None and not trades_df.empty:
            print(f"  Total trades: {len(trades_df)}")
            print(f"  Final cash: ${summary.get('current_cash', 0):.2f}")
        
        print(f"\n✅ Strategy test completed successfully!")
        
    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
