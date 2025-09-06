"""
ETF Analyzer - Comprehensive analysis of Round Hill ETFs
Analyzes performance metrics, dividend sustainability, and risk characteristics
"""

import pandas as pd
import numpy as np
from scipy import stats
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ETFAnalyzer:
    """Comprehensive ETF analysis and ranking system"""
    
    def __init__(self, config):
        self.config = config
        self.strategy = config['investment']['strategy']  # aggressive, moderate, conservative
        self.time_horizon = config['investment']['time_horizon_months']
        
    def analyze_etfs(self, etf_data, dividend_data):
        """
        Comprehensive analysis of all ETFs
        Returns detailed metrics for each ETF
        """
        logger.info(f"Analyzing {len(etf_data)} ETFs with {self.strategy} strategy focus...")
        
        etf_metrics = {}
        
        for symbol, data in etf_data.items():
            try:
                metrics = self._analyze_single_etf(symbol, data, dividend_data.get(symbol, {}))
                etf_metrics[symbol] = metrics
                logger.debug(f"✅ Analysis complete for {symbol}")
            except Exception as e:
                logger.error(f"Analysis failed for {symbol}: {e}")
        
        logger.info(f"Analysis completed for {len(etf_metrics)} ETFs")
        return etf_metrics
    
    def _analyze_single_etf(self, symbol, etf_data, dividend_data):
        """Analyze a single ETF comprehensively"""
        
        hist_data = etf_data['historical_data']
        info = etf_data['current_info']
        metadata = etf_data['metadata']
        
        # Price-based metrics
        price_metrics = self._calculate_price_metrics(hist_data)
        
        # Dividend metrics
        dividend_metrics = self._calculate_dividend_metrics(dividend_data, hist_data)
        
        # Risk metrics
        risk_metrics = self._calculate_risk_metrics(hist_data)
        
        # Technical indicators
        technical_metrics = self._calculate_technical_metrics(hist_data)
        
        # Fundamental metrics
        fundamental_metrics = self._calculate_fundamental_metrics(info, metadata)
        
        # Strategy-specific score
        strategy_score = self._calculate_strategy_score(
            price_metrics, dividend_metrics, risk_metrics, 
            technical_metrics, fundamental_metrics
        )
        
        return {
            'symbol': symbol,
            'name': metadata.get('name', 'Unknown'),
            'price_metrics': price_metrics,
            'dividend_metrics': dividend_metrics,
            'risk_metrics': risk_metrics,
            'technical_metrics': technical_metrics,
            'fundamental_metrics': fundamental_metrics,
            'strategy_score': strategy_score,
            'last_analysis': datetime.now()
        }
    
    def _calculate_price_metrics(self, hist_data):
        """Calculate comprehensive price-based performance metrics"""
        
        if hist_data.empty or 'Close' not in hist_data.columns:
            return self._empty_price_metrics()
        
        prices = hist_data['Close']
        returns = hist_data['Returns'].dropna()
        
        # Performance metrics
        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) if len(prices) > 0 else 0
        annualized_return = ((1 + total_return) ** (252 / len(prices)) - 1) if len(prices) > 0 else 0
        
        # Rolling performance
        returns_1m = returns.tail(21).mean() * 21 if len(returns) >= 21 else 0
        returns_3m = returns.tail(63).mean() * 63 if len(returns) >= 63 else 0
        returns_6m = returns.tail(126).mean() * 126 if len(returns) >= 126 else 0
        returns_1y = returns.tail(252).mean() * 252 if len(returns) >= 252 else annualized_return
        
        # Current price metrics
        current_price = prices.iloc[-1]
        price_52w_high = prices.tail(252).max() if len(prices) >= 252 else prices.max()
        price_52w_low = prices.tail(252).min() if len(prices) >= 252 else prices.min()
        price_vs_52w_high = (current_price / price_52w_high - 1) if price_52w_high > 0 else 0
        
        return {
            'current_price': current_price,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'return_1m': returns_1m,
            'return_3m': returns_3m,
            'return_6m': returns_6m,
            'return_1y': returns_1y,
            'price_52w_high': price_52w_high,
            'price_52w_low': price_52w_low,
            'price_vs_52w_high': price_vs_52w_high,
            'price_momentum': returns.tail(21).mean() if len(returns) >= 21 else 0
        }
    
    def _calculate_dividend_metrics(self, dividend_data, hist_data):
        """Calculate comprehensive dividend analysis"""
        
        if not dividend_data or 'dividend_yield' not in dividend_data:
            return self._empty_dividend_metrics()
        
        current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else 1
        
        # Core dividend metrics
        dividend_yield = dividend_data.get('dividend_yield', 0)
        dividend_frequency = dividend_data.get('dividend_frequency', 'Unknown')
        annualized_dividend = dividend_data.get('annualized_dividend', 0)
        dividend_growth_rate = dividend_data.get('dividend_growth_rate', 0)
        recent_dividend = dividend_data.get('recent_dividend', 0)
        
        # Weekly dividend analysis (key for Round Hill ETFs)
        is_weekly_dividend = dividend_frequency == 'Weekly'
        weekly_dividend_amount = recent_dividend if is_weekly_dividend else annualized_dividend / 52
        
        # Dividend sustainability metrics
        dividend_coverage = self._calculate_dividend_coverage(dividend_data, hist_data)
        dividend_consistency = self._calculate_dividend_consistency(dividend_data.get('dividends', pd.Series()))
        
        # Yield attractiveness (relative to risk-free rate)
        risk_free_rate = self.config['risk']['risk_free_rate']
        yield_spread = dividend_yield - risk_free_rate
        
        return {
            'dividend_yield': dividend_yield,
            'dividend_frequency': dividend_frequency,
            'is_weekly_dividend': is_weekly_dividend,
            'annualized_dividend': annualized_dividend,
            'weekly_dividend_amount': weekly_dividend_amount,
            'dividend_growth_rate': dividend_growth_rate,
            'recent_dividend': recent_dividend,
            'dividend_coverage': dividend_coverage,
            'dividend_consistency': dividend_consistency,
            'yield_spread': yield_spread,
            'dividend_score': self._calculate_dividend_score(dividend_yield, dividend_growth_rate, 
                                                          dividend_consistency, is_weekly_dividend)
        }
    
    def _calculate_risk_metrics(self, hist_data):
        """Calculate comprehensive risk metrics"""
        
        if hist_data.empty or 'Returns' not in hist_data.columns:
            return self._empty_risk_metrics()
        
        returns = hist_data['Returns'].dropna()
        
        if len(returns) < 30:
            return self._empty_risk_metrics()
        
        # Volatility metrics
        daily_volatility = returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252)
        
        # Rolling volatilities
        vol_1m = returns.tail(21).std() * np.sqrt(252) if len(returns) >= 21 else annualized_volatility
        vol_3m = returns.tail(63).std() * np.sqrt(252) if len(returns) >= 63 else annualized_volatility
        vol_6m = returns.tail(126).std() * np.sqrt(252) if len(returns) >= 126 else annualized_volatility
        
        # Downside metrics
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns / rolling_max - 1
        max_drawdown = drawdowns.min()
        
        # Value at Risk (VaR)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Sharpe ratio (using risk-free rate from config)
        risk_free_rate = self.config['risk']['risk_free_rate'] / 252  # Daily risk-free rate
        excess_returns = returns - risk_free_rate
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Sortino ratio (downside risk adjusted)
        sortino_ratio = excess_returns.mean() / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0
        
        return {
            'annualized_volatility': annualized_volatility,
            'volatility_1m': vol_1m,
            'volatility_3m': vol_3m,
            'volatility_6m': vol_6m,
            'downside_deviation': downside_deviation,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'var_99': var_99,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'risk_score': self._calculate_risk_score(annualized_volatility, max_drawdown, sharpe_ratio)
        }
    
    def _calculate_technical_metrics(self, hist_data):
        """Calculate technical analysis indicators"""
        
        if hist_data.empty or 'Close' not in hist_data.columns:
            return self._empty_technical_metrics()
        
        prices = hist_data['Close']
        
        # Moving averages
        sma_50 = hist_data.get('SMA_50', pd.Series()).iloc[-1] if 'SMA_50' in hist_data.columns else 0
        sma_200 = hist_data.get('SMA_200', pd.Series()).iloc[-1] if 'SMA_200' in hist_data.columns else 0
        
        current_price = prices.iloc[-1]
        
        # Trend indicators
        trend_50 = (current_price / sma_50 - 1) if sma_50 > 0 else 0
        trend_200 = (current_price / sma_200 - 1) if sma_200 > 0 else 0
        trend_strength = 'Bullish' if trend_50 > 0.02 else 'Bearish' if trend_50 < -0.02 else 'Neutral'
        
        # RSI calculation
        rsi = self._calculate_rsi(prices)
        
        # Volume analysis (if available)
        volume_trend = self._analyze_volume_trend(hist_data)
        
        return {
            'sma_50': sma_50,
            'sma_200': sma_200,
            'trend_50': trend_50,
            'trend_200': trend_200,
            'trend_strength': trend_strength,
            'rsi': rsi,
            'volume_trend': volume_trend,
            'technical_score': self._calculate_technical_score(trend_50, rsi, volume_trend)
        }
    
    def _calculate_fundamental_metrics(self, info, metadata):
        """Calculate fundamental analysis metrics"""
        
        # Basic fund metrics
        total_assets = info.get('totalAssets', 0)
        expense_ratio = info.get('annualReportExpenseRatio', info.get('expenseRatio', 0))
        inception_date = metadata.get('inceptionDate', None)
        
        # Calculate fund age
        fund_age_years = 0
        if inception_date:
            try:
                inception = pd.to_datetime(inception_date)
                fund_age_years = (datetime.now() - inception).days / 365.25
            except:
                fund_age_years = 0
        
        # Fund size score (larger funds generally more stable)
        size_score = min(total_assets / 100_000_000, 1.0) if total_assets > 0 else 0  # Scale to $100M
        
        # Expense ratio score (lower is better)
        expense_score = max(0, 1 - (expense_ratio / 0.01)) if expense_ratio > 0 else 0.5  # Scale to 1%
        
        # Maturity score (more mature funds have track record)
        maturity_score = min(fund_age_years / 3, 1.0)  # Scale to 3 years
        
        return {
            'total_assets': total_assets,
            'expense_ratio': expense_ratio,
            'fund_age_years': fund_age_years,
            'size_score': size_score,
            'expense_score': expense_score,
            'maturity_score': maturity_score,
            'fundamental_score': (size_score + expense_score + maturity_score) / 3
        }
    
    def _calculate_strategy_score(self, price_metrics, dividend_metrics, risk_metrics, 
                                 technical_metrics, fundamental_metrics):
        """Calculate strategy-specific composite score"""
        
        if self.strategy == 'aggressive':
            # Aggressive strategy weights: higher dividends, growth potential, acceptable risk
            weights = {
                'dividend_score': 0.35,
                'price_performance': 0.25,
                'risk_tolerance': 0.15,
                'technical_score': 0.15,
                'fundamental_score': 0.10
            }
        elif self.strategy == 'moderate':
            # Balanced approach
            weights = {
                'dividend_score': 0.30,
                'price_performance': 0.20,
                'risk_tolerance': 0.25,
                'technical_score': 0.15,
                'fundamental_score': 0.10
            }
        else:  # conservative
            # Conservative: focus on safety and consistent dividends
            weights = {
                'dividend_score': 0.40,
                'price_performance': 0.15,
                'risk_tolerance': 0.30,
                'technical_score': 0.10,
                'fundamental_score': 0.05
            }
        
        # Normalize scores to 0-1 range
        dividend_score = min(dividend_metrics.get('dividend_score', 0), 1.0)
        price_score = min((price_metrics.get('annualized_return', 0) + 0.5) / 1.0, 1.0)  # Scale around 0-50% returns
        risk_score = min(risk_metrics.get('risk_score', 0), 1.0)
        technical_score = min(technical_metrics.get('technical_score', 0), 1.0)
        fundamental_score = min(fundamental_metrics.get('fundamental_score', 0), 1.0)
        
        # Calculate weighted composite score
        composite_score = (
            weights['dividend_score'] * dividend_score +
            weights['price_performance'] * price_score +
            weights['risk_tolerance'] * risk_score +
            weights['technical_score'] * technical_score +
            weights['fundamental_score'] * fundamental_score
        )
        
        return {
            'composite_score': composite_score,
            'dividend_component': dividend_score * weights['dividend_score'],
            'price_component': price_score * weights['price_performance'],
            'risk_component': risk_score * weights['risk_tolerance'],
            'technical_component': technical_score * weights['technical_score'],
            'fundamental_component': fundamental_score * weights['fundamental_score'],
            'strategy': self.strategy,
            'recommendation': self._get_recommendation(composite_score)
        }
    
    def rank_etfs(self, etf_metrics):
        """Rank ETFs based on strategy-specific scoring"""
        
        # Create ranking DataFrame
        ranking_data = []
        for symbol, metrics in etf_metrics.items():
            ranking_data.append({
                'symbol': symbol,
                'name': metrics['name'],
                'composite_score': metrics['strategy_score']['composite_score'],
                'dividend_yield': metrics['dividend_metrics']['dividend_yield'],
                'annualized_return': metrics['price_metrics']['annualized_return'],
                'risk_score': metrics['risk_metrics']['risk_score'],
                'recommendation': metrics['strategy_score']['recommendation']
            })
        
        ranking_df = pd.DataFrame(ranking_data)
        ranking_df = ranking_df.sort_values('composite_score', ascending=False)
        
        logger.info(f"ETF ranking completed. Top ETF: {ranking_df.iloc[0]['symbol']}")
        
        return ranking_df
    
    # Helper methods for empty metrics
    def _empty_price_metrics(self):
        return {k: 0 for k in ['current_price', 'total_return', 'annualized_return', 
                              'return_1m', 'return_3m', 'return_6m', 'return_1y',
                              'price_52w_high', 'price_52w_low', 'price_vs_52w_high', 'price_momentum']}
    
    def _empty_dividend_metrics(self):
        return {k: 0 if k != 'dividend_frequency' else 'Unknown' 
                for k in ['dividend_yield', 'dividend_frequency', 'is_weekly_dividend', 
                         'annualized_dividend', 'weekly_dividend_amount', 'dividend_growth_rate',
                         'recent_dividend', 'dividend_coverage', 'dividend_consistency', 
                         'yield_spread', 'dividend_score']}
    
    def _empty_risk_metrics(self):
        return {k: 0 for k in ['annualized_volatility', 'volatility_1m', 'volatility_3m', 
                              'volatility_6m', 'downside_deviation', 'max_drawdown',
                              'var_95', 'var_99', 'sharpe_ratio', 'sortino_ratio', 'risk_score']}
    
    def _empty_technical_metrics(self):
        return {k: 0 if k != 'trend_strength' else 'Neutral' 
                for k in ['sma_50', 'sma_200', 'trend_50', 'trend_200', 
                         'trend_strength', 'rsi', 'volume_trend', 'technical_score']}
    
    # Additional helper calculation methods would go here...
    def _calculate_dividend_coverage(self, dividend_data, hist_data):
        """Calculate dividend coverage ratio"""
        # Simplified - would need more fundamental data for accurate calculation
        return 0.75  # Placeholder
    
    def _calculate_dividend_consistency(self, dividends):
        """Calculate dividend payment consistency"""
        if len(dividends) < 4:
            return 0
        # Calculate coefficient of variation (lower = more consistent)
        return max(0, 1 - (dividends.std() / dividends.mean())) if dividends.mean() > 0 else 0
    
    def _calculate_dividend_score(self, yield_val, growth_rate, consistency, is_weekly):
        """Calculate composite dividend score"""
        base_score = min(yield_val / 0.06, 1.0)  # Scale to 6% yield
        growth_bonus = min(growth_rate, 0.2) if growth_rate > 0 else 0
        consistency_bonus = consistency * 0.3
        weekly_bonus = 0.1 if is_weekly else 0
        
        return min(base_score + growth_bonus + consistency_bonus + weekly_bonus, 1.0)
    
    def _calculate_risk_score(self, volatility, max_drawdown, sharpe_ratio):
        """Calculate risk-adjusted score (higher is better)"""
        vol_score = max(0, 1 - (volatility / 0.3))  # Scale to 30% volatility
        drawdown_score = max(0, 1 - (abs(max_drawdown) / 0.5))  # Scale to 50% drawdown
        sharpe_score = min((sharpe_ratio + 1) / 3, 1.0) if sharpe_ratio > -1 else 0  # Scale sharpe
        
        return (vol_score + drawdown_score + sharpe_score) / 3
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def _analyze_volume_trend(self, hist_data):
        """Analyze volume trend if available"""
        if 'Volume' not in hist_data.columns or hist_data['Volume'].isna().all():
            return 0
        
        volume = hist_data['Volume'].dropna()
        if len(volume) < 20:
            return 0
        
        recent_avg = volume.tail(10).mean()
        historical_avg = volume.tail(50).mean()
        
        return (recent_avg / historical_avg - 1) if historical_avg > 0 else 0
    
    def _calculate_technical_score(self, trend_50, rsi, volume_trend):
        """Calculate composite technical score"""
        trend_score = min((trend_50 + 0.1) / 0.2, 1.0) if trend_50 > -0.1 else 0
        rsi_score = 1 - abs(rsi - 50) / 50 if 0 <= rsi <= 100 else 0
        volume_score = min((volume_trend + 0.2) / 0.4, 1.0) if volume_trend > -0.2 else 0
        
        return (trend_score + rsi_score + volume_score) / 3
    
    def _get_recommendation(self, score):
        """Get text recommendation based on score"""
        if score >= 0.8:
            return 'Strong Buy'
        elif score >= 0.6:
            return 'Buy'
        elif score >= 0.4:
            return 'Hold'
        elif score >= 0.2:
            return 'Weak Hold'
        else:
            return 'Avoid'
