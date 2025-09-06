"""
Monte Carlo Risk Engine - Simulates portfolio performance under various market scenarios
Provides risk metrics including VaR, maximum drawdown, and confidence intervals
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import norm, t
import logging
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class MonteCarloRiskEngine:
    """Advanced Monte Carlo simulation for portfolio risk analysis"""
    
    def __init__(self, config):
        self.config = config
        self.n_simulations = config['monte_carlo']['n_simulations']
        self.time_horizon_days = config['monte_carlo']['time_horizon_days']
        self.confidence_levels = config['monte_carlo']['confidence_levels']
        self.random_seed = config.get('random_seed', 42)
        
        # Set random seed for reproducibility
        np.random.seed(self.random_seed)
        
    def run_monte_carlo_analysis(self, portfolio, etf_data, etf_metrics):
        """
        Run comprehensive Monte Carlo analysis on portfolio
        """
        logger.info(f"Running Monte Carlo analysis with {self.n_simulations:,} simulations over {self.time_horizon_days} days")
        
        # Prepare simulation parameters
        simulation_params = self._prepare_simulation_parameters(portfolio, etf_data, etf_metrics)
        
        if not simulation_params:
            logger.error("Failed to prepare simulation parameters")
            return None
        
        # Run simulations
        simulation_results = self._run_simulations(simulation_params)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(simulation_results, portfolio)
        
        # Generate visualizations
        visualizations = self._create_visualizations(simulation_results, risk_metrics)
        
        # Stress testing
        stress_tests = self._run_stress_tests(simulation_params, portfolio)
        
        return {
            'simulation_results': simulation_results,
            'risk_metrics': risk_metrics,
            'visualizations': visualizations,
            'stress_tests': stress_tests,
            'simulation_params': simulation_params,
            'analysis_date': datetime.now(),
            'n_simulations': self.n_simulations
        }
    
    def _prepare_simulation_parameters(self, portfolio, etf_data, etf_metrics):
        """Prepare parameters for Monte Carlo simulation"""
        
        weights = portfolio['weights']
        allocation = portfolio['allocation']
        
        # Build returns matrix for covariance calculation
        returns_data = {}
        expected_returns = {}
        
        for symbol, weight in weights.items():
            if weight > 0 and symbol in etf_data:
                hist_data = etf_data[symbol]['historical_data']
                
                if 'Returns' in hist_data.columns and not hist_data['Returns'].empty:
                    returns = hist_data['Returns'].dropna()
                    
                    if len(returns) >= 30:  # Minimum data requirement
                        returns_data[symbol] = returns
                        
                        # Calculate expected return (annualized)
                        mean_return = returns.mean() * 252
                        
                        # Adjust for dividend yield
                        dividend_yield = etf_metrics.get(symbol, {}).get('dividend_metrics', {}).get('dividend_yield', 0)
                        expected_returns[symbol] = mean_return + dividend_yield
        
        if not returns_data:
            logger.error("No suitable return data found for simulation")
            return None
        
        # Convert to DataFrame and calculate covariance matrix
        returns_df = pd.DataFrame(returns_data).dropna()
        
        if len(returns_df) < 30:
            logger.error("Insufficient overlapping data for simulation")
            return None
        
        # Covariance matrix (annualized)
        cov_matrix = returns_df.cov() * 252
        
        # Filter weights to match available data
        available_symbols = list(returns_data.keys())
        filtered_weights = {symbol: weights[symbol] for symbol in available_symbols}
        
        # Normalize weights
        total_weight = sum(filtered_weights.values())
        if total_weight > 0:
            filtered_weights = {symbol: weight / total_weight for symbol, weight in filtered_weights.items()}
        
        logger.info(f"Simulation prepared for {len(available_symbols)} ETFs: {', '.join(available_symbols)}")
        
        return {
            'symbols': available_symbols,
            'weights': filtered_weights,
            'expected_returns': expected_returns,
            'cov_matrix': cov_matrix,
            'returns_df': returns_df,
            'portfolio_value': allocation['total_invested']
        }
    
    def _run_simulations(self, params):
        """Run Monte Carlo simulations"""
        
        symbols = params['symbols']
        weights = params['weights']
        expected_returns = params['expected_returns']
        cov_matrix = params['cov_matrix']
        initial_value = params['portfolio_value']
        
        # Convert to arrays for numpy operations
        weight_array = np.array([weights[symbol] for symbol in symbols])
        return_array = np.array([expected_returns[symbol] for symbol in symbols])
        cov_array = cov_matrix.loc[symbols, symbols].values
        
        # Portfolio expected return and volatility
        portfolio_return = np.dot(weight_array, return_array)
        portfolio_variance = np.dot(weight_array.T, np.dot(cov_array, weight_array))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        logger.info(f"Portfolio expected return: {portfolio_return:.3f}, volatility: {portfolio_volatility:.3f}")
        
        # Simulate daily returns using geometric Brownian motion
        dt = 1 / 252  # Daily time step
        n_days = self.time_horizon_days
        
        # Pre-allocate results arrays
        portfolio_paths = np.zeros((self.n_simulations, n_days + 1))
        portfolio_paths[:, 0] = initial_value
        
        # Generate random returns
        random_returns = np.random.multivariate_normal(
            return_array * dt,
            cov_array * dt,
            size=(self.n_simulations, n_days)
        )
        
        # Calculate portfolio returns
        portfolio_daily_returns = np.dot(random_returns, weight_array)
        
        # Generate portfolio value paths
        for day in range(n_days):
            portfolio_paths[:, day + 1] = portfolio_paths[:, day] * (1 + portfolio_daily_returns[:, day])
        
        # Calculate returns and drawdowns
        final_values = portfolio_paths[:, -1]
        total_returns = (final_values / initial_value) - 1
        
        # Calculate maximum drawdown for each simulation
        max_drawdowns = np.zeros(self.n_simulations)
        for i in range(self.n_simulations):
            path = portfolio_paths[i, :]
            running_max = np.maximum.accumulate(path)
            drawdowns = (path - running_max) / running_max
            max_drawdowns[i] = drawdowns.min()
        
        return {
            'portfolio_paths': portfolio_paths,
            'final_values': final_values,
            'total_returns': total_returns,
            'max_drawdowns': max_drawdowns,
            'portfolio_return': portfolio_return,
            'portfolio_volatility': portfolio_volatility,
            'daily_returns': portfolio_daily_returns
        }
    
    def _calculate_risk_metrics(self, simulation_results, portfolio):
        """Calculate comprehensive risk metrics from simulation results"""
        
        total_returns = simulation_results['total_returns']
        max_drawdowns = simulation_results['max_drawdowns']
        final_values = simulation_results['final_values']
        initial_value = portfolio['allocation']['total_invested']
        
        # Value at Risk calculations
        var_metrics = {}
        for confidence in self.confidence_levels:
            var_percentile = (1 - confidence) * 100
            var_value = np.percentile(total_returns, var_percentile)
            var_dollar = initial_value * var_value
            
            var_metrics[f'var_{int(confidence*100)}'] = {
                'percentage': var_value,
                'dollar_amount': var_dollar,
                'confidence_level': confidence
            }
        
        # Expected Shortfall (Conditional VaR)
        expected_shortfall = {}
        for confidence in self.confidence_levels:
            var_threshold = var_metrics[f'var_{int(confidence*100)}']['percentage']
            tail_returns = total_returns[total_returns <= var_threshold]
            es_value = tail_returns.mean() if len(tail_returns) > 0 else var_threshold
            
            expected_shortfall[f'es_{int(confidence*100)}'] = {
                'percentage': es_value,
                'dollar_amount': initial_value * es_value
            }
        
        # Drawdown statistics
        drawdown_stats = {
            'max_drawdown_mean': max_drawdowns.mean(),
            'max_drawdown_median': np.median(max_drawdowns),
            'max_drawdown_worst': max_drawdowns.min(),
            'max_drawdown_95_percentile': np.percentile(max_drawdowns, 5),  # 5th percentile (worst 5%)
            'probability_loss': (total_returns < 0).mean(),
            'probability_large_loss': (total_returns < -0.1).mean()  # Probability of >10% loss
        }
        
        # Return statistics
        return_stats = {
            'expected_return': total_returns.mean(),
            'return_std': total_returns.std(),
            'return_skewness': stats.skew(total_returns),
            'return_kurtosis': stats.kurtosis(total_returns),
            'median_return': np.median(total_returns),
            'probability_profit': (total_returns > 0).mean(),
            'probability_large_gain': (total_returns > 0.1).mean()  # Probability of >10% gain
        }
        
        # Confidence intervals for final portfolio value
        confidence_intervals = {}
        for confidence in self.confidence_levels:
            lower_percentile = (1 - confidence) / 2 * 100
            upper_percentile = (1 + confidence) / 2 * 100
            
            confidence_intervals[f'ci_{int(confidence*100)}'] = {
                'lower_bound': np.percentile(final_values, lower_percentile),
                'upper_bound': np.percentile(final_values, upper_percentile),
                'lower_return': np.percentile(total_returns, lower_percentile),
                'upper_return': np.percentile(total_returns, upper_percentile)
            }
        
        # Risk-adjusted metrics
        sharpe_ratio = return_stats['expected_return'] / return_stats['return_std'] if return_stats['return_std'] > 0 else 0
        sortino_ratio = return_stats['expected_return'] / np.std(total_returns[total_returns < 0]) if len(total_returns[total_returns < 0]) > 0 else 0
        
        risk_adjusted_metrics = {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': return_stats['expected_return'] / abs(drawdown_stats['max_drawdown_worst']) if drawdown_stats['max_drawdown_worst'] < 0 else 0
        }
        
        logger.info(f"Risk analysis complete. VaR 95%: {var_metrics['var_95']['percentage']:.3f}")
        
        return {
            'var_metrics': var_metrics,
            'expected_shortfall': expected_shortfall,
            'drawdown_stats': drawdown_stats,
            'return_stats': return_stats,
            'confidence_intervals': confidence_intervals,
            'risk_adjusted_metrics': risk_adjusted_metrics
        }
    
    def _create_visualizations(self, simulation_results, risk_metrics):
        """Create visualization data for Monte Carlo results"""
        
        # This would typically generate actual plots, but for now return data for plotting
        total_returns = simulation_results['total_returns']
        max_drawdowns = simulation_results['max_drawdowns']
        portfolio_paths = simulation_results['portfolio_paths']
        
        visualization_data = {
            'return_distribution': {
                'data': total_returns,
                'type': 'histogram',
                'title': 'Portfolio Return Distribution',
                'x_label': 'Total Return',
                'y_label': 'Frequency'
            },
            'drawdown_distribution': {
                'data': max_drawdowns,
                'type': 'histogram',
                'title': 'Maximum Drawdown Distribution',
                'x_label': 'Maximum Drawdown',
                'y_label': 'Frequency'
            },
            'portfolio_paths': {
                'data': portfolio_paths,
                'type': 'line_plot',
                'title': f'Portfolio Value Paths ({self.n_simulations:,} Simulations)',
                'x_label': 'Days',
                'y_label': 'Portfolio Value ($)'
            },
            'var_visualization': {
                'var_95': risk_metrics['var_metrics']['var_95']['percentage'],
                'var_99': risk_metrics['var_metrics']['var_99']['percentage'],
                'type': 'var_plot',
                'title': 'Value at Risk Visualization'
            }
        }
        
        return visualization_data
    
    def _run_stress_tests(self, params, portfolio):
        """Run various stress test scenarios"""
        
        symbols = params['symbols']
        weights = params['weights']
        expected_returns = params['expected_returns']
        cov_matrix = params['cov_matrix']
        initial_value = params['portfolio_value']
        
        weight_array = np.array([weights[symbol] for symbol in symbols])
        return_array = np.array([expected_returns[symbol] for symbol in symbols])
        cov_array = cov_matrix.loc[symbols, symbols].values
        
        stress_scenarios = {
            'market_crash_2008': {
                'description': '2008 Financial Crisis scenario',
                'return_shock': -0.37,  # ~37% market decline
                'volatility_multiplier': 2.0
            },
            'covid_crash_2020': {
                'description': 'COVID-19 market crash',
                'return_shock': -0.34,  # ~34% decline in March 2020
                'volatility_multiplier': 3.0
            },
            'interest_rate_shock': {
                'description': 'Rapid interest rate increase',
                'return_shock': -0.15,  # Dividend stocks sensitive to rates
                'volatility_multiplier': 1.5
            },
            'dividend_cut_scenario': {
                'description': 'Widespread dividend cuts',
                'return_shock': -0.25,  # Focus on dividend impact
                'volatility_multiplier': 1.8
            },
            'bull_market': {
                'description': 'Strong bull market scenario',
                'return_shock': 0.25,   # 25% gain
                'volatility_multiplier': 0.8
            }
        }
        
        stress_results = {}
        
        for scenario_name, scenario in stress_scenarios.items():
            # Apply stress scenario
            stressed_returns = return_array + scenario['return_shock']
            stressed_cov = cov_array * scenario['volatility_multiplier']
            
            # Calculate portfolio impact
            portfolio_return = np.dot(weight_array, stressed_returns)
            portfolio_variance = np.dot(weight_array.T, np.dot(stressed_cov, weight_array))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Simulate under stress
            n_stress_simulations = min(1000, self.n_simulations)  # Fewer simulations for speed
            
            random_returns = np.random.multivariate_normal(
                stressed_returns / 252,  # Daily returns
                stressed_cov / 252,      # Daily covariance
                size=(n_stress_simulations, self.time_horizon_days)
            )
            
            portfolio_stress_returns = np.dot(random_returns, weight_array)
            
            # Calculate stress metrics
            cumulative_returns = np.prod(1 + portfolio_stress_returns, axis=1) - 1
            final_values = initial_value * (1 + cumulative_returns)
            
            stress_var_95 = np.percentile(cumulative_returns, 5)
            stress_expected_return = cumulative_returns.mean()
            
            stress_results[scenario_name] = {
                'description': scenario['description'],
                'expected_return': stress_expected_return,
                'var_95': stress_var_95,
                'final_value_mean': final_values.mean(),
                'final_value_5th_percentile': np.percentile(final_values, 5),
                'probability_loss': (cumulative_returns < 0).mean(),
                'portfolio_volatility': portfolio_volatility
            }
        
        logger.info(f"Stress testing completed for {len(stress_scenarios)} scenarios")
        
        return stress_results
    
    def generate_risk_report(self, monte_carlo_results):
        """Generate comprehensive risk report"""
        
        risk_metrics = monte_carlo_results['risk_metrics']
        stress_tests = monte_carlo_results['stress_tests']
        
        report = {
            'executive_summary': self._create_executive_summary(risk_metrics),
            'detailed_metrics': risk_metrics,
            'stress_test_summary': self._summarize_stress_tests(stress_tests),
            'recommendations': self._generate_risk_recommendations(risk_metrics, stress_tests)
        }
        
        return report
    
    def _create_executive_summary(self, risk_metrics):
        """Create executive summary of risk analysis"""
        
        var_95 = risk_metrics['var_metrics']['var_95']['percentage']
        expected_return = risk_metrics['return_stats']['expected_return']
        max_drawdown = risk_metrics['drawdown_stats']['max_drawdown_worst']
        probability_loss = risk_metrics['drawdown_stats']['probability_loss']
        
        risk_level = 'Low' if var_95 > -0.1 else 'Moderate' if var_95 > -0.2 else 'High'
        
        summary = f"""
        MONTE CARLO RISK ANALYSIS SUMMARY
        
        Expected Portfolio Return: {expected_return:.2%}
        Value at Risk (95%): {var_95:.2%}
        Worst Case Drawdown: {max_drawdown:.2%}
        Probability of Loss: {probability_loss:.1%}
        Overall Risk Level: {risk_level}
        
        The portfolio shows {'favorable' if expected_return > 0.06 else 'moderate'} return potential 
        with {'manageable' if var_95 > -0.15 else 'elevated'} downside risk.
        """
        
        return summary.strip()
    
    def _summarize_stress_tests(self, stress_tests):
        """Summarize stress test results"""
        
        worst_scenario = min(stress_tests.items(), key=lambda x: x[1]['var_95'])
        best_scenario = max(stress_tests.items(), key=lambda x: x[1]['expected_return'])
        
        summary = {
            'worst_case_scenario': {
                'name': worst_scenario[0],
                'description': worst_scenario[1]['description'],
                'var_95': worst_scenario[1]['var_95']
            },
            'best_case_scenario': {
                'name': best_scenario[0],
                'description': best_scenario[1]['description'],
                'expected_return': best_scenario[1]['expected_return']
            },
            'average_stress_var': np.mean([test['var_95'] for test in stress_tests.values()]),
            'resilience_score': 1 - abs(np.mean([test['var_95'] for test in stress_tests.values() if test['var_95'] < 0]))
        }
        
        return summary
    
    def _generate_risk_recommendations(self, risk_metrics, stress_tests):
        """Generate risk management recommendations"""
        
        recommendations = []
        
        # VaR-based recommendations
        var_95 = risk_metrics['var_metrics']['var_95']['percentage']
        if var_95 < -0.2:
            recommendations.append("Consider reducing position sizes or adding defensive assets to lower VaR")
        
        # Drawdown recommendations
        max_drawdown = risk_metrics['drawdown_stats']['max_drawdown_worst']
        if max_drawdown < -0.3:
            recommendations.append("Implement stop-loss rules or dynamic hedging to limit drawdowns")
        
        # Concentration recommendations
        recommendations.append("Monitor portfolio concentration and consider additional diversification")
        
        # Stress test recommendations
        worst_stress = min(stress_tests.values(), key=lambda x: x['var_95'])
        if worst_stress['var_95'] < -0.4:
            recommendations.append("Consider stress testing scenarios when rebalancing portfolio")
        
        # General recommendations
        recommendations.extend([
            "Regular portfolio rebalancing to maintain target allocations",
            "Monitor correlation changes between ETF holdings",
            "Consider adding uncorrelated assets during market stress periods"
        ])
        
        return recommendations
