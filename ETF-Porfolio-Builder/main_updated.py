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
        logging.FileHandler('etf_portfolio_builder.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("🚀 Starting ETF Portfolio Builder Analysis")
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        logger.info(f"Configuration loaded for {config['investment']['strategy']} strategy")
        logger.info(f"Investment capital: ${config['investment']['capital']:,}")
        
        # Create output directory
        output_dir = config.get('output_dir', 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Data Collection
        logger.info("📊 Step 1: Collecting Round Hill ETF data...")
        data_collector = ETFDataCollector(config)
        
        # Discover Round Hill ETFs
        etf_universe = data_collector.discover_round_hill_etfs()
        logger.info(f"Discovered {len(etf_universe)} Round Hill ETFs")
        
        # Collect comprehensive data for each ETF
        etf_data = {}
        dividend_data = {}
        
        for symbol in etf_universe:
            try:
                etf_info = data_collector.collect_etf_data(symbol)
                if etf_info:
                    etf_data[symbol] = etf_info
                    
                    # Collect dividend data
                    div_info = data_collector.collect_dividend_data(symbol)
                    if div_info:
                        dividend_data[symbol] = div_info
                    
                    logger.info(f"✅ Data collected for {symbol}")
            except Exception as e:
                logger.error(f"❌ Failed to collect data for {symbol}: {e}")
        
        logger.info(f"Successfully collected data for {len(etf_data)} ETFs")
        
        # Step 2: ETF Analysis
        logger.info("📈 Step 2: Analyzing ETF performance and metrics...")
        etf_analyzer = ETFAnalyzer(config)
        etf_metrics = etf_analyzer.analyze_etfs(etf_data, dividend_data)
        
        # Rank ETFs based on strategy
        etf_rankings = etf_analyzer.rank_etfs(etf_metrics)
        logger.info(f"ETF analysis completed. Top-ranked ETF: {etf_rankings.iloc[0]['symbol']}")
        
        # Step 3: Portfolio Optimization
        logger.info("⚖️ Step 3: Optimizing portfolio allocation...")
        portfolio_optimizer = PortfolioOptimizer(config)
        optimal_portfolio = portfolio_optimizer.optimize_portfolio(etf_metrics, etf_data)
        
        if optimal_portfolio:
            total_invested = optimal_portfolio['allocation']['total_invested']
            n_positions = len([w for w in optimal_portfolio['weights'].values() if w > 0])
            logger.info(f"Portfolio optimization completed: ${total_invested:,.2f} allocated across {n_positions} positions")
        else:
            logger.error("Portfolio optimization failed")
            return
        
        # Step 4: Forecasting
        logger.info("🔮 Step 4: Generating 12-month forecasts...")
        forecasting_engine = ForecastingEngine(config)
        forecasts = forecasting_engine.generate_forecasts(etf_data, etf_metrics)
        logger.info(f"12-month forecasts generated for {len(forecasts['etf_forecasts'])} ETFs")
        
        # Step 5: Risk Analysis
        logger.info("📊 Step 5: Running Monte Carlo risk analysis...")
        monte_carlo_engine = MonteCarloRiskEngine(config)
        monte_carlo_results = monte_carlo_engine.run_monte_carlo_analysis(optimal_portfolio, etf_data, etf_metrics)
        
        if monte_carlo_results:
            risk_metrics = monte_carlo_results['risk_metrics']
            var_95 = risk_metrics['var_metrics']['var_95']['percentage']
            logger.info(f"Monte Carlo analysis completed. Portfolio VaR (95%): {var_95:.2%}")
        else:
            logger.warning("Monte Carlo analysis failed or incomplete")
        
        # Step 6: Visualization and Reporting
        logger.info("📈 Step 6: Creating interactive dashboard and reports...")
        dashboard = VisualizationDashboard(config)
        
        # Create comprehensive visualizations
        charts = dashboard.create_comprehensive_dashboard(etf_metrics, optimal_portfolio, forecasts, monte_carlo_results)
        
        # Export charts
        exported_files = dashboard.export_charts(charts, format='html')
        logger.info(f"Exported {len(exported_files)} visualization files")
        
        # Create summary report
        summary_report = dashboard.create_summary_report(etf_metrics, optimal_portfolio, forecasts, monte_carlo_results)
        
        # Save summary report
        report_file = os.path.join(output_dir, 'portfolio_analysis_report.md')
        with open(report_file, 'w') as f:
            f.write(summary_report)
        logger.info(f"Summary report saved to {report_file}")
        
        # Save detailed results
        results = {
            'etf_rankings': etf_rankings.to_dict('records'),
            'optimal_portfolio': optimal_portfolio,
            'forecasts_summary': {
                'market_forecast': forecasts.get('market_forecast', {}),
                'forecast_horizon_months': forecasts.get('horizon_months', 12)
            },
            'risk_summary': monte_carlo_results.get('risk_metrics', {}) if monte_carlo_results else {},
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'strategy': config['investment']['strategy'],
                'capital': config['investment']['capital'],
                'etfs_analyzed': len(etf_data),
                'etfs_selected': len([w for w in optimal_portfolio['weights'].values() if w > 0])
            }
        }
        
        # Save as JSON for programmatic access
        results_file = os.path.join(output_dir, 'analysis_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Detailed results saved to {results_file}")
        
        # Generate final summary
        print("\n" + "="*60)
        print("🎯 ETF PORTFOLIO ANALYSIS COMPLETE")
        print("="*60)
        print(f"Strategy: {config['investment']['strategy'].title()}")
        print(f"Capital: ${config['investment']['capital']:,}")
        print(f"ETFs Analyzed: {len(etf_data)}")
        print(f"ETFs Selected: {len([w for w in optimal_portfolio['weights'].values() if w > 0])}")
        print(f"Amount Invested: ${optimal_portfolio['allocation']['total_invested']:,.2f}")
        print(f"Cash Remaining: ${optimal_portfolio['allocation']['leftover_cash']:,.2f}")
        print(f"Expected Annual Return: {optimal_portfolio['metrics']['expected_annual_return']:.2%}")
        print(f"Dividend Yield: {optimal_portfolio['metrics']['dividend_yield']:.2%}")
        
        if monte_carlo_results:
            print(f"Value at Risk (95%): {monte_carlo_results['risk_metrics']['var_metrics']['var_95']['percentage']:.2%}")
        
        print(f"\nReports saved to: {output_dir}/")
        print("="*60)
        
        # Display portfolio allocation
        if optimal_portfolio['allocation']['shares']:
            print("\n📊 OPTIMAL PORTFOLIO ALLOCATION:")
            print("-" * 40)
            for symbol, shares in optimal_portfolio['allocation']['shares'].items():
                value = optimal_portfolio['allocation']['values'][symbol]
                percentage = optimal_portfolio['allocation']['allocation_percentage'][symbol]
                price = optimal_portfolio['allocation']['prices'][symbol]
                print(f"{symbol:6} | {shares:4} shares @ ${price:6.2f} = ${value:8,.0f} ({percentage:5.1%})")
        
        # Display top ETF rankings
        print(f"\n🏆 TOP {min(10, len(etf_rankings))} ETF RANKINGS:")
        print("-" * 60)
        print("Rank | Symbol | Score | Yield  | Return | Recommendation")
        print("-" * 60)
        for idx, row in etf_rankings.head(10).iterrows():
            print(f"{idx+1:4} | {row['symbol']:6} | {row['composite_score']:5.3f} | "
                  f"{row['dividend_yield']:5.2%} | {row['annualized_return']:6.2%} | {row['recommendation']}")
        
        logger.info("✅ Analysis pipeline completed successfully!")
        
        # Return results for potential further use
        return {
            'etf_data': etf_data,
            'etf_metrics': etf_metrics,
            'portfolio': optimal_portfolio,
            'forecasts': forecasts,
            'monte_carlo': monte_carlo_results,
            'charts': charts
        }
        
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def run_analysis_step_by_step():
    """Run analysis with user interaction between steps"""
    logger.info("🚀 Starting Interactive ETF Portfolio Analysis")
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        print(f"\n📋 Configuration Summary:")
        print(f"Strategy: {config['investment']['strategy']}")
        print(f"Capital: ${config['investment']['capital']:,}")
        print(f"Max ETFs: {config['constraints']['max_etfs_in_portfolio']}")
        print(f"Max Position Size: {config['constraints']['max_position_size']:.1%}")
        
        input("\nPress Enter to start data collection...")
        
        # Step 1: Data Collection
        print("\n📊 Step 1: Discovering and collecting Round Hill ETF data...")
        data_collector = ETFDataCollector(config)
        etf_universe = data_collector.discover_round_hill_etfs()
        print(f"Found {len(etf_universe)} Round Hill ETFs")
        
        # Show discovered ETFs
        print(f"Discovered ETFs: {', '.join(etf_universe[:10])}" + (f" ... and {len(etf_universe)-10} more" if len(etf_universe) > 10 else ""))
        
        proceed = input(f"\nProceed with data collection for all {len(etf_universe)} ETFs? (y/n): ")
        if proceed.lower() != 'y':
            print("Analysis cancelled.")
            return
        
        # Continue with automated analysis
        return main()
        
    except Exception as e:
        logger.error(f"❌ Interactive analysis error: {e}")
        raise

def run_quick_analysis():
    """Run a quick analysis with limited ETFs for testing"""
    logger.info("🚀 Starting Quick ETF Portfolio Analysis (Limited ETFs)")
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        # Override some settings for quick analysis
        config['data']['max_etfs_to_analyze'] = 5  # Limit to 5 ETFs for quick testing
        config['monte_carlo']['n_simulations'] = 1000  # Fewer simulations for speed
        
        print(f"\n⚡ QUICK ANALYSIS MODE")
        print(f"Limited to {config['data']['max_etfs_to_analyze']} ETFs for testing")
        print(f"Strategy: {config['investment']['strategy']}")
        print(f"Capital: ${config['investment']['capital']:,}")
        
        # Run main analysis with modified config
        return main()
        
    except Exception as e:
        logger.error(f"❌ Quick analysis error: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "--interactive":
            run_analysis_step_by_step()
        elif mode == "--quick":
            run_quick_analysis()
        else:
            print("Usage: python main.py [--interactive|--quick]")
            print("  --interactive: Run with user prompts between steps")
            print("  --quick: Run quick analysis with limited ETFs")
    else:
        main()
