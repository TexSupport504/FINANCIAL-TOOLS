"""
Main application for ETF Portfolio Builder
Orchestrates the complete analysis pipeline for Round Hill ETF portfolio optimization
"""

import logging
import yaml
import os
from datetime import datetime
import pandas as pd
import numpy as np
import json
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our custom modules
from data.etf_data_collector import ETFDataCollector
from analysis.etf_analyzer import ETFAnalyzer
from analysis.portfolio_optimizer import PortfolioOptimizer
from analysis.forecasting_engine import ForecastingEngine
from analysis.monte_carlo_engine import MonteCarloRiskEngine
from visualization.dashboard import VisualizationDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('portfolio_builder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_file='config.yaml'):
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Configuration loaded from {config_file}")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def main():
    """Main application function"""
    logger.info("Starting Round Hill ETF Portfolio Builder")
    
    # Load configuration
    config = load_config()
    capital = config['investment']['capital']
    target_etfs = config['portfolio']['target_etfs']
    
    print(f"\n🎯 Round Hill ETF Portfolio Builder")
    print(f"💰 Investment Capital: ${capital:,}")
    print(f"📊 Strategy: {config['investment']['strategy'].title()}")
    print(f"⏰ Time Horizon: {config['investment']['time_horizon_months']} months")
    print(f"📈 Target ETFs: {', '.join(target_etfs)}")
    print("-" * 50)
    
    try:
        # Step 1: Data Collection
        print("\n1️⃣ Collecting Round Hill ETF Data...")
        data_collector = ETFDataCollector(config)
        
        # Research Round Hill ETF universe
        round_hill_etfs = data_collector.discover_round_hill_etfs()
        print(f"   Found {len(round_hill_etfs)} Round Hill ETFs")
        
        # Collect historical data
        etf_data = data_collector.collect_etf_data(round_hill_etfs)
        dividend_data = data_collector.collect_dividend_data(round_hill_etfs)
        
        # Step 2: ETF Analysis
        print("\n2️⃣ Analyzing ETF Performance...")
        analyzer = ETFAnalyzer(config)
        
        # Analyze each ETF
        etf_metrics = analyzer.analyze_etfs(etf_data, dividend_data)
        top_etfs = analyzer.rank_etfs(etf_metrics)
        
        print(f"   Top performing ETFs identified: {len(top_etfs)}")
        
        # Step 3: Portfolio Optimization
        print("\n3️⃣ Optimizing Portfolio Allocation...")
        optimizer = PortfolioOptimizer(config)
        
        # Optimize allocation
        optimal_weights = optimizer.optimize_portfolio(etf_data, etf_metrics)
        portfolio_allocation = optimizer.calculate_allocation(optimal_weights, capital)
        
        print(f"   Optimal allocation calculated for ${capital:,}")
        
        # Step 4: Forecasting
        print("\n4️⃣ Generating 12-Month Forecasts...")
        forecast_engine = ForecastEngine(config)
        
        # Generate forecasts
        price_forecasts = forecast_engine.forecast_prices(etf_data, etf_metrics)
        dividend_forecasts = forecast_engine.forecast_dividends(dividend_data, etf_metrics)
        
        # Step 5: Risk Analysis
        print("\n5️⃣ Running Monte Carlo Risk Analysis...")
        risk_modeler = RiskModeler(config)
        
        # Monte Carlo simulation
        mc_results = risk_modeler.monte_carlo_simulation(
            etf_data, optimal_weights, capital
        )
        
        # Calculate risk metrics
        risk_metrics = risk_modeler.calculate_risk_metrics(mc_results)
        
        # Step 6: Generate Results
        print("\n6️⃣ Generating Results and Visualizations...")
        
        # Create comprehensive results
        results = {
            'portfolio_allocation': portfolio_allocation,
            'etf_metrics': etf_metrics,
            'forecasts': {
                'prices': price_forecasts,
                'dividends': dividend_forecasts
            },
            'risk_analysis': {
                'monte_carlo': mc_results,
                'risk_metrics': risk_metrics
            },
            'config': config,
            'timestamp': datetime.now()
        }
        
        # Save results
        if config['output']['save_results']:
            results_df = pd.DataFrame(results['portfolio_allocation'])
            results_df.to_csv(f"data/portfolio_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            print("   Results saved to CSV file")
        
        # Launch dashboard
        if config['output']['dashboard']:
            dashboard = Dashboard(config)
            dashboard.create_dashboard(results)
            print("   Dashboard created - launching...")
            
        # Print summary
        print_results_summary(results)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise
    
    logger.info("Portfolio analysis completed successfully")

def print_results_summary(results):
    """Print a summary of the results"""
    print("\n" + "="*50)
    print("📋 PORTFOLIO RECOMMENDATION SUMMARY")
    print("="*50)
    
    allocation = results['portfolio_allocation']
    total_dividend_yield = sum([etf['expected_dividend_yield'] * etf['weight'] 
                               for etf in allocation if etf['weight'] > 0])
    
    print(f"\n💼 Recommended Portfolio Allocation:")
    for etf in allocation:
        if etf['weight'] > 0:
            print(f"   {etf['symbol']}: ${etf['dollar_amount']:,.0f} ({etf['weight']:.1%})")
    
    print(f"\n📊 Expected Performance (12 months):")
    print(f"   • Total Dividend Yield: {total_dividend_yield:.2%}")
    print(f"   • Expected Total Return: TBD")
    print(f"   • Risk Level: {results['config']['investment']['strategy'].title()}")
    
    risk_metrics = results['risk_analysis']['risk_metrics']
    print(f"\n⚠️  Risk Metrics:")
    print(f"   • Value at Risk (95%): ${risk_metrics.get('var_95', 0):,.0f}")
    print(f"   • Maximum Drawdown: {risk_metrics.get('max_drawdown', 0):.1%}")
    
    print("\n🚀 Ready to deploy your optimized Round Hill ETF portfolio!")

if __name__ == "__main__":
    main()
