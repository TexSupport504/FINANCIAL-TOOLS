"""
Portfolio Optimizer - Modern Portfolio Theory implementation for Round Hill ETFs
Optimizes portfolio allocation using risk-return characteristics with constraints
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import cvxpy as cp # type: ignore
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
import logging
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    """Advanced portfolio optimization using Modern Portfolio Theory"""
    
    def __init__(self, config):
        self.config = config
        self.capital = config['investment']['capital']
        self.strategy = config['investment']['strategy']
        self.max_position_size = config['constraints']['max_position_size']
        self.min_position_size = config['constraints']['min_position_size']
        self.max_etfs = config['constraints']['max_etfs_in_portfolio']
        self.rebalance_frequency = config['investment']['rebalance_frequency']
        
    def optimize_portfolio(self, etf_metrics, etf_data):
        """
        Main optimization function - creates optimal portfolio allocation
        """
        logger.info(f"Optimizing portfolio for {self.strategy} strategy with ${self.capital:,.2f}")
        
        # Prepare data for optimization
        returns_data, selected_etfs = self._prepare_optimization_data(etf_metrics, etf_data)
        
        if returns_data.empty:
            logger.error("No suitable ETFs found for optimization")
            return None
        
        logger.info(f"Selected {len(selected_etfs)} ETFs for optimization: {', '.join(selected_etfs)}")
        
        # Calculate expected returns and risk model
        mu = self._calculate_expected_returns(returns_data, etf_metrics)
        S = self._calculate_covariance_matrix(returns_data)
        
        # Perform strategy-specific optimization
        if self.strategy == 'aggressive':
            optimal_weights = self._optimize_aggressive(mu, S, selected_etfs)
        elif self.strategy == 'moderate':
            optimal_weights = self._optimize_moderate(mu, S, selected_etfs)
        else:  # conservative
            optimal_weights = self._optimize_conservative(mu, S, selected_etfs)
        
        # Create discrete allocation
        allocation = self._create_discrete_allocation(optimal_weights, etf_data, selected_etfs)
        
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(optimal_weights, mu, S, etf_metrics)
        
        return {
            'weights': optimal_weights,
            'allocation': allocation,
            'metrics': portfolio_metrics,
            'selected_etfs': selected_etfs,
            'optimization_date': datetime.now(),
            'strategy': self.strategy
        }
    
    def _prepare_optimization_data(self, etf_metrics, etf_data):
        """Prepare and filter data for optimization"""
        
        # Filter ETFs based on strategy criteria
        selected_etfs = self._select_etfs_for_optimization(etf_metrics)
        
        # Build returns matrix
        returns_data = pd.DataFrame()
        
        for symbol in selected_etfs:
            if symbol in etf_data and 'historical_data' in etf_data[symbol]:
                hist_data = etf_data[symbol]['historical_data']
                if 'Returns' in hist_data.columns and not hist_data['Returns'].empty:
                    returns_data[symbol] = hist_data['Returns'].dropna()
        
        # Align dates and ensure sufficient data
        if not returns_data.empty:
            returns_data = returns_data.dropna()
            # Require at least 60 trading days of data
            if len(returns_data) < 60:
                logger.warning(f"Insufficient data for optimization: {len(returns_data)} days")
                return pd.DataFrame(), []
        
        logger.info(f"Prepared {len(returns_data)} days of returns data for {len(selected_etfs)} ETFs")
        return returns_data, selected_etfs
    
    def _select_etfs_for_optimization(self, etf_metrics):
        """Select best ETFs based on strategy and constraints"""
        
        # Create selection DataFrame
        selection_data = []
        for symbol, metrics in etf_metrics.items():
            selection_data.append({
                'symbol': symbol,
                'composite_score': metrics['strategy_score']['composite_score'],
                'dividend_yield': metrics['dividend_metrics']['dividend_yield'],
                'risk_score': metrics['risk_metrics']['risk_score'],
                'total_assets': metrics['fundamental_metrics']['total_assets'],
                'recommendation': metrics['strategy_score']['recommendation']
            })
        
        selection_df = pd.DataFrame(selection_data)
        
        # Apply selection criteria
        # 1. Must have positive composite score
        selection_df = selection_df[selection_df['composite_score'] > 0.3]
        
        # 2. Must have sufficient assets (avoid micro-ETFs)
        min_assets = 10_000_000  # $10M minimum
        selection_df = selection_df[selection_df['total_assets'] >= min_assets]
        
        # 3. Must not be 'Avoid' recommendation
        selection_df = selection_df[selection_df['recommendation'] != 'Avoid']
        
        # 4. Sort by composite score and select top candidates
        selection_df = selection_df.sort_values('composite_score', ascending=False)
        
        # Strategy-specific selection
        if self.strategy == 'aggressive':
            # Aggressive: Higher yield preference, willing to take more ETFs
            max_selection = min(self.max_etfs, 12)
            selection_df = selection_df[selection_df['dividend_yield'] >= 0.03]  # 3% minimum yield
        elif self.strategy == 'moderate':
            # Moderate: Balanced selection
            max_selection = min(self.max_etfs, 8)
            selection_df = selection_df[selection_df['dividend_yield'] >= 0.025]  # 2.5% minimum yield
        else:  # conservative
            # Conservative: Quality focus, fewer ETFs
            max_selection = min(self.max_etfs, 6)
            selection_df = selection_df[selection_df['risk_score'] >= 0.5]  # Higher risk score (lower risk)
        
        selected_etfs = selection_df.head(max_selection)['symbol'].tolist()
        
        logger.info(f"Selected {len(selected_etfs)} ETFs from {len(etf_metrics)} candidates")
        return selected_etfs
    
    def _calculate_expected_returns(self, returns_data, etf_metrics):
        """Calculate expected returns incorporating multiple factors"""
        
        # Historical returns
        historical_returns = expected_returns.mean_historical_return(returns_data, frequency=252)
        
        # Adjust based on strategy and forward-looking factors
        adjusted_returns = historical_returns.copy()
        
        for symbol in returns_data.columns:
            if symbol in etf_metrics:
                metrics = etf_metrics[symbol]
                
                # Dividend yield contribution
                dividend_yield = metrics['dividend_metrics']['dividend_yield']
                
                # Adjust for dividend sustainability and growth
                dividend_adjustment = dividend_yield * metrics['dividend_metrics']['dividend_consistency']
                
                # Technical momentum adjustment
                momentum_factor = metrics['technical_metrics']['trend_50'] * 0.1  # Small momentum adjustment
                
                # Combine adjustments
                adjusted_returns[symbol] = (
                    historical_returns[symbol] * 0.6 +  # 60% historical
                    dividend_adjustment * 0.3 +        # 30% dividend
                    momentum_factor * 0.1               # 10% momentum
                )
        
        logger.debug(f"Expected returns range: {adjusted_returns.min():.3f} to {adjusted_returns.max():.3f}")
        return adjusted_returns
    
    def _calculate_covariance_matrix(self, returns_data):
        """Calculate covariance matrix with shrinkage"""
        
        # Use Ledoit-Wolf shrinkage for more stable covariance estimation
        S = risk_models.CovarianceShrinkage(returns_data).ledoit_wolf()
        
        logger.debug(f"Covariance matrix shape: {S.shape}")
        return S
    
    def _optimize_aggressive(self, mu, S, selected_etfs):
        """Aggressive strategy optimization - maximize returns with controlled risk"""
        
        try:
            ef = EfficientFrontier(mu, S)
            
            # Set constraints
            ef.add_constraint(lambda w: w >= self.min_position_size)  # Minimum position
            ef.add_constraint(lambda w: w <= self.max_position_size)  # Maximum position
            
            # Aggressive: Maximize Sharpe ratio with higher risk tolerance
            ef.max_sharpe()
            
            weights = ef.clean_weights()
            logger.info("Aggressive optimization completed using max Sharpe ratio")
            
        except Exception as e:
            logger.warning(f"Sharpe optimization failed: {e}. Using equal weight fallback.")
            weights = self._equal_weight_fallback(selected_etfs)
        
        return weights
    
    def _optimize_moderate(self, mu, S, selected_etfs):
        """Moderate strategy optimization - balanced risk-return"""
        
        try:
            ef = EfficientFrontier(mu, S)
            
            # Set constraints
            ef.add_constraint(lambda w: w >= self.min_position_size)
            ef.add_constraint(lambda w: w <= self.max_position_size)
            
            # Moderate: Target specific return level
            target_return = mu.mean()  # Target average expected return
            ef.efficient_return(target_return)
            
            weights = ef.clean_weights()
            logger.info(f"Moderate optimization completed targeting {target_return:.3f} return")
            
        except Exception as e:
            logger.warning(f"Target return optimization failed: {e}. Using min volatility.")
            try:
                ef = EfficientFrontier(mu, S)
                ef.add_constraint(lambda w: w >= self.min_position_size)
                ef.add_constraint(lambda w: w <= self.max_position_size)
                ef.min_volatility()
                weights = ef.clean_weights()
            except:
                weights = self._equal_weight_fallback(selected_etfs)
        
        return weights
    
    def _optimize_conservative(self, mu, S, selected_etfs):
        """Conservative strategy optimization - minimize risk"""
        
        try:
            ef = EfficientFrontier(mu, S)
            
            # Set constraints
            ef.add_constraint(lambda w: w >= self.min_position_size)
            ef.add_constraint(lambda w: w <= self.max_position_size * 0.8)  # Lower max for conservative
            
            # Conservative: Minimize volatility
            ef.min_volatility()
            
            weights = ef.clean_weights()
            logger.info("Conservative optimization completed using min volatility")
            
        except Exception as e:
            logger.warning(f"Min volatility optimization failed: {e}. Using equal weight fallback.")
            weights = self._equal_weight_fallback(selected_etfs)
        
        return weights
    
    def _equal_weight_fallback(self, selected_etfs):
        """Fallback to equal weighting if optimization fails"""
        
        n_etfs = len(selected_etfs)
        equal_weight = 1.0 / n_etfs
        
        # Apply constraints
        if equal_weight > self.max_position_size:
            # Use max position size for top ETFs, zero for others
            n_max = int(1.0 / self.max_position_size)
            weights = {}
            for i, etf in enumerate(selected_etfs):
                weights[etf] = self.max_position_size if i < n_max else 0
        else:
            weights = {etf: equal_weight for etf in selected_etfs}
        
        logger.info(f"Applied equal weight fallback: {equal_weight:.3f} per ETF")
        return weights
    
    def _create_discrete_allocation(self, weights, etf_data, selected_etfs):
        """Convert weights to actual share allocations"""
        
        try:
            # Get latest prices
            latest_prices = {}
            for symbol in selected_etfs:
                if symbol in etf_data and 'historical_data' in etf_data[symbol]:
                    hist_data = etf_data[symbol]['historical_data']
                    if not hist_data.empty and 'Close' in hist_data.columns:
                        latest_prices[symbol] = hist_data['Close'].iloc[-1]
                    else:
                        # Fallback price
                        latest_prices[symbol] = 50.0
                else:
                    latest_prices[symbol] = 50.0
            
            latest_prices = pd.Series(latest_prices)
            
            # Create discrete allocation
            da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=self.capital)
            allocation, leftover = da.greedy_portfolio()
            
            # Calculate allocation summary
            total_invested = sum(shares * latest_prices[symbol] for symbol, shares in allocation.items())
            
            allocation_summary = {
                'shares': allocation,
                'prices': latest_prices.to_dict(),
                'values': {symbol: shares * latest_prices[symbol] for symbol, shares in allocation.items()},
                'total_invested': total_invested,
                'leftover_cash': leftover,
                'allocation_percentage': {
                    symbol: (shares * latest_prices[symbol] / total_invested) 
                    for symbol, shares in allocation.items()
                } if total_invested > 0 else {}
            }
            
            logger.info(f"Discrete allocation: ${total_invested:,.2f} invested, ${leftover:,.2f} cash remaining")
            
        except Exception as e:
            logger.error(f"Discrete allocation failed: {e}")
            allocation_summary = {
                'shares': {},
                'prices': {},
                'values': {},
                'total_invested': 0,
                'leftover_cash': self.capital,
                'allocation_percentage': {}
            }
        
        return allocation_summary
    
    def _calculate_portfolio_metrics(self, weights, mu, S, etf_metrics):
        """Calculate comprehensive portfolio performance metrics"""
        
        weights_array = np.array([weights.get(symbol, 0) for symbol in mu.index])
        
        # Expected return and volatility
        expected_return = np.dot(weights_array, mu.values)
        portfolio_variance = np.dot(weights_array.T, np.dot(S.values, weights_array))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Sharpe ratio
        risk_free_rate = self.config['risk']['risk_free_rate']
        sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Portfolio dividend yield
        portfolio_dividend_yield = 0
        for symbol, weight in weights.items():
            if weight > 0 and symbol in etf_metrics:
                dividend_yield = etf_metrics[symbol]['dividend_metrics']['dividend_yield']
                portfolio_dividend_yield += weight * dividend_yield
        
        # Diversification metrics
        effective_positions = sum(1 for w in weights.values() if w >= self.min_position_size)
        concentration_ratio = max(weights.values()) if weights else 0
        
        # VaR calculation (95% confidence)
        portfolio_var_95 = -1.645 * portfolio_volatility  # Daily VaR
        portfolio_var_95_annual = portfolio_var_95 * np.sqrt(252)
        
        return {
            'expected_annual_return': expected_return,
            'annual_volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'dividend_yield': portfolio_dividend_yield,
            'var_95_daily': portfolio_var_95,
            'var_95_annual': portfolio_var_95_annual,
            'effective_positions': effective_positions,
            'concentration_ratio': concentration_ratio,
            'diversification_score': 1 - concentration_ratio,
            'risk_return_score': sharpe_ratio * (1 - concentration_ratio),
        }
    
    def generate_rebalancing_schedule(self, portfolio):
        """Generate rebalancing recommendations"""
        
        rebalance_schedule = []
        
        if self.rebalance_frequency == 'monthly':
            periods = 12
        elif self.rebalance_frequency == 'quarterly':
            periods = 4
        elif self.rebalance_frequency == 'semi-annually':
            periods = 2
        else:  # annually
            periods = 1
        
        for i in range(periods):
            months_ahead = 12 // periods * i
            rebalance_date = datetime.now() + pd.DateOffset(months=months_ahead)
            
            rebalance_schedule.append({
                'date': rebalance_date,
                'action': 'Review and rebalance portfolio',
                'frequency': self.rebalance_frequency,
                'target_weights': portfolio['weights']
            })
        
        return rebalance_schedule
