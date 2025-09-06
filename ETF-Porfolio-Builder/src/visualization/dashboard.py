"""
Visualization Dashboard - Interactive charts and reports for ETF portfolio analysis
Creates comprehensive visualizations for analysis results and portfolio performance
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import logging
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Set style preferences
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class VisualizationDashboard:
    """Comprehensive visualization dashboard for ETF portfolio analysis"""
    
    def __init__(self, config):
        self.config = config
        self.output_dir = config.get('output_dir', 'output')
        self.strategy = config['investment']['strategy']
        
    def create_comprehensive_dashboard(self, etf_metrics, portfolio, forecasts, monte_carlo_results):
        """Create complete dashboard with all visualizations"""
        
        logger.info("Creating comprehensive visualization dashboard...")
        
        # Create individual chart components
        charts = {
            'etf_analysis_charts': self._create_etf_analysis_charts(etf_metrics),
            'portfolio_allocation_charts': self._create_portfolio_charts(portfolio, etf_metrics),
            'forecast_charts': self._create_forecast_charts(forecasts),
            'risk_analysis_charts': self._create_risk_charts(monte_carlo_results),
            'performance_summary': self._create_performance_summary(etf_metrics, portfolio, forecasts),
            'interactive_dashboard': self._create_interactive_dashboard(etf_metrics, portfolio, forecasts, monte_carlo_results)
        }
        
        logger.info("Dashboard creation completed")
        return charts
    
    def _create_etf_analysis_charts(self, etf_metrics):
        """Create ETF analysis and ranking visualizations"""
        
        # Prepare data for visualization
        etf_data = []
        for symbol, metrics in etf_metrics.items():
            etf_data.append({
                'Symbol': symbol,
                'Name': metrics['name'][:20] + '...' if len(metrics['name']) > 20 else metrics['name'],
                'Composite Score': metrics['strategy_score']['composite_score'],
                'Dividend Yield': metrics['dividend_metrics']['dividend_yield'],
                'Annual Return': metrics['price_metrics']['annualized_return'],
                'Risk Score': metrics['risk_metrics']['risk_score'],
                'Volatility': metrics['risk_metrics']['annualized_volatility'],
                'Sharpe Ratio': metrics['risk_metrics']['sharpe_ratio'],
                'Recommendation': metrics['strategy_score']['recommendation'],
                'Total Assets': metrics['fundamental_metrics']['total_assets'] / 1_000_000,  # In millions
                'Weekly Dividend': metrics['dividend_metrics']['is_weekly_dividend']
            })
        
        df = pd.DataFrame(etf_data).sort_values('Composite Score', ascending=False)
        
        charts = {}
        
        # 1. ETF Ranking Chart
        fig_ranking = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        color_map = {'Strong Buy': colors[0], 'Buy': colors[1], 'Hold': colors[2], 
                    'Weak Hold': colors[3], 'Avoid': colors[4]}
        
        fig_ranking.add_trace(go.Bar(
            x=df['Symbol'].head(15),
            y=df['Composite Score'].head(15),
            text=df['Recommendation'].head(15),
            textposition='auto',
            marker_color=[color_map.get(rec, '#1f77b4') for rec in df['Recommendation'].head(15)],
            name='Composite Score'
        ))
        
        fig_ranking.update_layout(
            title=f'Top 15 Round Hill ETFs - {self.strategy.title()} Strategy Ranking',
            xaxis_title='ETF Symbol',
            yaxis_title='Composite Score',
            template='plotly_white',
            height=500
        )
        charts['etf_ranking'] = fig_ranking
        
        # 2. Risk-Return Scatter Plot
        fig_risk_return = px.scatter(
            df, x='Volatility', y='Annual Return',
            size='Total Assets', color='Dividend Yield',
            hover_name='Symbol', hover_data=['Composite Score', 'Recommendation'],
            title='Risk-Return Profile of Round Hill ETFs',
            labels={'Volatility': 'Annualized Volatility', 'Annual Return': 'Annualized Return'}
        )
        
        # Add quadrant lines
        fig_risk_return.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_risk_return.add_vline(x=df['Volatility'].median(), line_dash="dash", line_color="gray")
        
        fig_risk_return.update_layout(template='plotly_white', height=500)
        charts['risk_return_scatter'] = fig_risk_return
        
        # 3. Dividend Analysis
        dividend_etfs = df[df['Dividend Yield'] > 0.02].copy()  # ETFs with >2% yield
        
        fig_dividend = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Dividend Yield Distribution', 'Weekly vs Other Frequency',
                          'Yield vs Risk Score', 'Top Dividend Yielders'),
            specs=[[{"type": "histogram"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # Dividend yield histogram
        fig_dividend.add_trace(
            go.Histogram(x=dividend_etfs['Dividend Yield'], nbinsx=20, name='Yield Distribution'),
            row=1, col=1
        )
        
        # Weekly vs other dividend frequency
        weekly_count = len(dividend_etfs[dividend_etfs['Weekly Dividend']])
        other_count = len(dividend_etfs[~dividend_etfs['Weekly Dividend']])
        
        fig_dividend.add_trace(
            go.Bar(x=['Weekly', 'Other'], y=[weekly_count, other_count], name='Frequency'),
            row=1, col=2
        )
        
        # Yield vs risk score
        fig_dividend.add_trace(
            go.Scatter(x=dividend_etfs['Risk Score'], y=dividend_etfs['Dividend Yield'],
                      mode='markers', text=dividend_etfs['Symbol'],
                      name='Yield vs Risk'),
            row=2, col=1
        )
        
        # Top dividend yielders
        top_dividend = dividend_etfs.nlargest(10, 'Dividend Yield')
        fig_dividend.add_trace(
            go.Bar(x=top_dividend['Symbol'], y=top_dividend['Dividend Yield'],
                  name='Top Yielders'),
            row=2, col=2
        )
        
        fig_dividend.update_layout(
            title='Dividend Analysis Dashboard',
            height=800,
            template='plotly_white',
            showlegend=False
        )
        charts['dividend_analysis'] = fig_dividend
        
        return charts
    
    def _create_portfolio_charts(self, portfolio, etf_metrics):
        """Create portfolio allocation and composition charts"""
        
        charts = {}
        allocation = portfolio['allocation']
        weights = portfolio['weights']
        
        # 1. Portfolio Allocation Pie Chart
        if allocation['shares']:
            symbols = list(allocation['shares'].keys())
            values = [allocation['values'][symbol] for symbol in symbols]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=symbols, 
                values=values,
                hole=.3,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie.update_layout(
                title=f'Portfolio Allocation - ${allocation["total_invested"]:,.0f} Invested',
                template='plotly_white',
                height=500
            )
            charts['portfolio_pie'] = fig_pie
        
        # 2. Portfolio Metrics Summary
        metrics = portfolio['metrics']
        
        fig_metrics = go.Figure()
        
        metric_names = ['Expected Return', 'Dividend Yield', 'Sharpe Ratio', 'Risk Score']
        metric_values = [
            metrics['expected_annual_return'],
            metrics['dividend_yield'],
            metrics['sharpe_ratio'],
            metrics.get('risk_return_score', 0.5)
        ]
        
        fig_metrics.add_trace(go.Bar(
            x=metric_names,
            y=metric_values,
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
            text=[f'{val:.3f}' for val in metric_values],
            textposition='auto'
        ))
        
        fig_metrics.update_layout(
            title='Portfolio Performance Metrics',
            yaxis_title='Value',
            template='plotly_white',
            height=400
        )
        charts['portfolio_metrics'] = fig_metrics
        
        # 3. Diversification Analysis
        if allocation['shares']:
            # Create diversification heatmap
            selected_etfs = list(allocation['shares'].keys())
            
            # Get sector/category information if available
            categories = []
            for symbol in selected_etfs:
                # Simplified category extraction - would be more sophisticated in practice
                if 'DIV' in symbol or 'YIELD' in symbol:
                    categories.append('Dividend Focus')
                elif 'TECH' in symbol or 'QQQ' in symbol:
                    categories.append('Technology')
                elif 'REIT' in symbol or 'RE' in symbol:
                    categories.append('Real Estate')
                else:
                    categories.append('Broad Market')
            
            category_weights = {}
            for i, symbol in enumerate(selected_etfs):
                category = categories[i] if i < len(categories) else 'Other'
                weight = allocation['allocation_percentage'].get(symbol, 0)
                category_weights[category] = category_weights.get(category, 0) + weight
            
            fig_diversification = go.Figure(data=[go.Bar(
                x=list(category_weights.keys()),
                y=list(category_weights.values()),
                marker_color='lightblue'
            )])
            
            fig_diversification.update_layout(
                title='Portfolio Diversification by Category',
                xaxis_title='Category',
                yaxis_title='Allocation (%)',
                template='plotly_white',
                height=400
            )
            charts['diversification'] = fig_diversification
        
        return charts
    
    def _create_forecast_charts(self, forecasts):
        """Create forecasting visualization charts"""
        
        charts = {}
        etf_forecasts = forecasts['etf_forecasts']
        
        # 1. Price Forecast Summary
        forecast_data = []
        for symbol, forecast in etf_forecasts.items():
            if forecast['price_forecast']['monthly_forecasts']:
                monthly_data = forecast['price_forecast']['monthly_forecasts']
                for month_data in monthly_data:
                    forecast_data.append({
                        'Symbol': symbol,
                        'Month': month_data['month'],
                        'Price': month_data['price'],
                        'Return': month_data['return'],
                        'Confidence': month_data['confidence']
                    })
        
        if forecast_data:
            forecast_df = pd.DataFrame(forecast_data)
            
            # Price evolution chart
            fig_price_forecast = px.line(
                forecast_df, x='Month', y='Price', color='Symbol',
                title='12-Month Price Forecasts by ETF',
                labels={'Month': 'Month Ahead', 'Price': 'Forecasted Price ($)'}
            )
            fig_price_forecast.update_layout(template='plotly_white', height=500)
            charts['price_forecasts'] = fig_price_forecast
            
            # Return forecast heatmap
            pivot_returns = forecast_df.pivot(index='Symbol', columns='Month', values='Return')
            
            fig_return_heatmap = go.Figure(data=go.Heatmap(
                z=pivot_returns.values,
                x=[f'Month {i}' for i in range(1, 13)],
                y=pivot_returns.index,
                colorscale='RdYlGn',
                zmid=0
            ))
            
            fig_return_heatmap.update_layout(
                title='Monthly Return Forecasts Heatmap',
                template='plotly_white',
                height=500
            )
            charts['return_heatmap'] = fig_return_heatmap
        
        # 2. Dividend Forecast Analysis
        dividend_forecasts = []
        for symbol, forecast in etf_forecasts.items():
            dividend_data = forecast.get('dividend_forecast', {})
            if dividend_data.get('monthly_forecasts'):
                for month_data in dividend_data['monthly_forecasts']:
                    dividend_forecasts.append({
                        'Symbol': symbol,
                        'Month': month_data['month'],
                        'Yield': month_data['projected_yield'],
                        'Sustainability': month_data['sustainability_score']
                    })
        
        if dividend_forecasts:
            dividend_df = pd.DataFrame(dividend_forecasts)
            
            fig_dividend_forecast = px.line(
                dividend_df, x='Month', y='Yield', color='Symbol',
                title='12-Month Dividend Yield Forecasts',
                labels={'Month': 'Month Ahead', 'Yield': 'Projected Dividend Yield'}
            )
            fig_dividend_forecast.update_layout(template='plotly_white', height=500)
            charts['dividend_forecasts'] = fig_dividend_forecast
        
        return charts
    
    def _create_risk_charts(self, monte_carlo_results):
        """Create risk analysis and Monte Carlo visualization charts"""
        
        charts = {}
        
        if not monte_carlo_results or 'simulation_results' not in monte_carlo_results:
            return charts
        
        sim_results = monte_carlo_results['simulation_results']
        risk_metrics = monte_carlo_results['risk_metrics']
        
        # 1. Return Distribution
        returns = sim_results['total_returns']
        
        fig_return_dist = go.Figure()
        fig_return_dist.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name='Return Distribution',
            opacity=0.7
        ))
        
        # Add VaR lines
        var_95 = risk_metrics['var_metrics']['var_95']['percentage']
        var_99 = risk_metrics['var_metrics']['var_99']['percentage']
        
        fig_return_dist.add_vline(x=var_95, line_dash="dash", line_color="red",
                                 annotation_text=f"VaR 95%: {var_95:.2%}")
        fig_return_dist.add_vline(x=var_99, line_dash="dash", line_color="darkred",
                                 annotation_text=f"VaR 99%: {var_99:.2%}")
        
        fig_return_dist.update_layout(
            title='Portfolio Return Distribution (Monte Carlo)',
            xaxis_title='Total Return',
            yaxis_title='Frequency',
            template='plotly_white',
            height=500
        )
        charts['return_distribution'] = fig_return_dist
        
        # 2. Drawdown Distribution
        drawdowns = sim_results['max_drawdowns']
        
        fig_drawdown_dist = go.Figure()
        fig_drawdown_dist.add_trace(go.Histogram(
            x=drawdowns,
            nbinsx=50,
            name='Drawdown Distribution',
            opacity=0.7,
            marker_color='orange'
        ))
        
        worst_drawdown = risk_metrics['drawdown_stats']['max_drawdown_worst']
        fig_drawdown_dist.add_vline(x=worst_drawdown, line_dash="dash", line_color="red",
                                   annotation_text=f"Worst Case: {worst_drawdown:.2%}")
        
        fig_drawdown_dist.update_layout(
            title='Maximum Drawdown Distribution',
            xaxis_title='Maximum Drawdown',
            yaxis_title='Frequency',
            template='plotly_white',
            height=500
        )
        charts['drawdown_distribution'] = fig_drawdown_dist
        
        # 3. Portfolio Path Visualization (sample paths)
        paths = sim_results['portfolio_paths']
        n_paths_to_show = min(100, paths.shape[0])  # Show up to 100 paths
        
        fig_paths = go.Figure()
        
        # Add sample paths
        for i in range(0, n_paths_to_show, max(1, n_paths_to_show // 20)):  # Show ~20 paths
            fig_paths.add_trace(go.Scatter(
                y=paths[i, :],
                mode='lines',
                opacity=0.1,
                line=dict(color='blue'),
                showlegend=False,
                name=f'Path {i+1}'
            ))
        
        # Add mean path
        mean_path = np.mean(paths, axis=0)
        fig_paths.add_trace(go.Scatter(
            y=mean_path,
            mode='lines',
            line=dict(color='red', width=3),
            name='Mean Path'
        ))
        
        # Add confidence intervals
        percentile_5 = np.percentile(paths, 5, axis=0)
        percentile_95 = np.percentile(paths, 95, axis=0)
        
        fig_paths.add_trace(go.Scatter(
            y=percentile_95,
            mode='lines',
            line=dict(color='green', dash='dash'),
            name='95th Percentile'
        ))
        
        fig_paths.add_trace(go.Scatter(
            y=percentile_5,
            mode='lines',
            fill='tonexty',
            line=dict(color='green', dash='dash'),
            name='5th Percentile'
        ))
        
        fig_paths.update_layout(
            title=f'Portfolio Value Evolution ({monte_carlo_results["n_simulations"]:,} Simulations)',
            xaxis_title='Days',
            yaxis_title='Portfolio Value ($)',
            template='plotly_white',
            height=600
        )
        charts['portfolio_paths'] = fig_paths
        
        # 4. Risk Metrics Summary
        risk_summary = risk_metrics['risk_adjusted_metrics']
        
        fig_risk_summary = go.Figure()
        
        risk_names = ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']
        risk_values = [
            risk_summary['sharpe_ratio'],
            risk_summary['sortino_ratio'],
            risk_summary['calmar_ratio']
        ]
        
        fig_risk_summary.add_trace(go.Bar(
            x=risk_names,
            y=risk_values,
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
            text=[f'{val:.3f}' for val in risk_values],
            textposition='auto'
        ))
        
        fig_risk_summary.update_layout(
            title='Risk-Adjusted Performance Metrics',
            yaxis_title='Ratio Value',
            template='plotly_white',
            height=400
        )
        charts['risk_summary'] = fig_risk_summary
        
        return charts
    
    def _create_performance_summary(self, etf_metrics, portfolio, forecasts):
        """Create performance summary dashboard"""
        
        # Calculate key summary statistics
        n_etfs_analyzed = len(etf_metrics)
        n_etfs_selected = len([w for w in portfolio['weights'].values() if w > 0])
        
        avg_dividend_yield = np.mean([
            metrics['dividend_metrics']['dividend_yield'] 
            for metrics in etf_metrics.values()
        ])
        
        portfolio_yield = portfolio['metrics']['dividend_yield']
        expected_return = portfolio['metrics']['expected_annual_return']
        
        summary_data = {
            'Analysis Summary': {
                'ETFs Analyzed': n_etfs_analyzed,
                'ETFs Selected': n_etfs_selected,
                'Average Market Yield': f'{avg_dividend_yield:.2%}',
                'Portfolio Yield': f'{portfolio_yield:.2%}',
                'Expected Annual Return': f'{expected_return:.2%}',
                'Strategy': portfolio['strategy'].title(),
                'Capital Allocated': f"${portfolio['allocation']['total_invested']:,.0f}",
                'Cash Remaining': f"${portfolio['allocation']['leftover_cash']:,.0f}"
            }
        }
        
        return summary_data
    
    def _create_interactive_dashboard(self, etf_metrics, portfolio, forecasts, monte_carlo_results):
        """Create comprehensive interactive dashboard"""
        
        # This would create a full interactive dashboard
        # For now, return the structure for the dashboard
        
        dashboard_components = {
            'title': f'{self.strategy.title()} Strategy - Round Hill ETF Portfolio Analysis',
            'sections': [
                {
                    'name': 'Portfolio Overview',
                    'charts': ['portfolio_pie', 'portfolio_metrics', 'diversification']
                },
                {
                    'name': 'ETF Analysis',
                    'charts': ['etf_ranking', 'risk_return_scatter', 'dividend_analysis']
                },
                {
                    'name': 'Forecasting',
                    'charts': ['price_forecasts', 'return_heatmap', 'dividend_forecasts']
                },
                {
                    'name': 'Risk Analysis',
                    'charts': ['return_distribution', 'drawdown_distribution', 'portfolio_paths', 'risk_summary']
                }
            ],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return dashboard_components
    
    def export_charts(self, charts, format='html'):
        """Export charts to files"""
        
        logger.info(f"Exporting charts in {format} format...")
        
        exported_files = []
        
        for chart_category, category_charts in charts.items():
            if chart_category == 'interactive_dashboard':
                continue
            
            for chart_name, chart in category_charts.items():
                if hasattr(chart, 'write_html') and format == 'html':
                    filename = f"{chart_category}_{chart_name}.html"
                    filepath = f"{self.output_dir}/{filename}"
                    chart.write_html(filepath)
                    exported_files.append(filepath)
                elif hasattr(chart, 'write_image') and format in ['png', 'pdf']:
                    filename = f"{chart_category}_{chart_name}.{format}"
                    filepath = f"{self.output_dir}/{filename}"
                    chart.write_image(filepath)
                    exported_files.append(filepath)
        
        logger.info(f"Exported {len(exported_files)} chart files")
        return exported_files
    
    def create_summary_report(self, etf_metrics, portfolio, forecasts, monte_carlo_results):
        """Create comprehensive text summary report"""
        
        report_sections = []
        
        # Executive Summary
        report_sections.append("# ETF Portfolio Analysis Report")
        report_sections.append(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append(f"**Strategy:** {self.strategy.title()}")
        report_sections.append(f"**Investment Capital:** ${portfolio['allocation']['total_invested']:,.2f}")
        report_sections.append("")
        
        # Portfolio Composition
        report_sections.append("## Portfolio Composition")
        if portfolio['allocation']['shares']:
            for symbol, shares in portfolio['allocation']['shares'].items():
                value = portfolio['allocation']['values'][symbol]
                percentage = portfolio['allocation']['allocation_percentage'][symbol]
                report_sections.append(f"- **{symbol}**: {shares} shares, ${value:,.2f} ({percentage:.1%})")
        report_sections.append("")
        
        # Key Metrics
        metrics = portfolio['metrics']
        report_sections.append("## Portfolio Metrics")
        report_sections.append(f"- **Expected Annual Return:** {metrics['expected_annual_return']:.2%}")
        report_sections.append(f"- **Dividend Yield:** {metrics['dividend_yield']:.2%}")
        report_sections.append(f"- **Sharpe Ratio:** {metrics['sharpe_ratio']:.3f}")
        report_sections.append(f"- **Annual Volatility:** {metrics['annual_volatility']:.2%}")
        report_sections.append("")
        
        # Risk Analysis
        if monte_carlo_results and 'risk_metrics' in monte_carlo_results:
            risk_metrics = monte_carlo_results['risk_metrics']
            report_sections.append("## Risk Analysis")
            report_sections.append(f"- **Value at Risk (95%):** {risk_metrics['var_metrics']['var_95']['percentage']:.2%}")
            report_sections.append(f"- **Maximum Drawdown:** {risk_metrics['drawdown_stats']['max_drawdown_worst']:.2%}")
            report_sections.append(f"- **Probability of Loss:** {risk_metrics['drawdown_stats']['probability_loss']:.1%}")
        
        report_text = "\n".join(report_sections)
        
        return report_text
