# Round Hill ETF Portfolio Builder

A comprehensive Python application for analyzing, optimizing, and forecasting Round Hill ETF dividend portfolios using modern portfolio theory, Monte Carlo risk analysis, and machine learning forecasting.

## 🎯 Overview

This application provides a complete end-to-end solution for building optimized Round Hill ETF portfolios with a focus on dividend income. It combines quantitative analysis, risk modeling, and forecasting to help investors make data-driven decisions.

### Key Features

- **🔍 ETF Universe Discovery**: Automatically discovers and analyzes all Round Hill ETFs
- **📊 Comprehensive Analysis**: Performance metrics, dividend analysis, risk assessment, and technical indicators
- **⚖️ Portfolio Optimization**: Modern Portfolio Theory with customizable constraints and strategy-specific optimization
- **🔮 12-Month Forecasting**: Machine learning-based price and dividend forecasts
- **📈 Monte Carlo Risk Analysis**: 10,000+ simulation risk modeling with VaR and stress testing
- **📱 Interactive Dashboard**: Comprehensive visualizations and reporting
- **💼 Multiple Investment Strategies**: Aggressive, Moderate, and Conservative approaches

## 🚀 Quick Start

### 1. Installation

```bash
git clone <repository-url>
cd ETF-Portfolio-Builder
pip install -r requirements.txt
```

### 2. Configuration

Edit `config.yaml` to customize your investment strategy:

```yaml
investment:
  capital: 16500          # Investment amount
  strategy: aggressive    # aggressive, moderate, conservative
  time_horizon_months: 12

constraints:
  max_position_size: 0.30        # 30% max per ETF
  max_etfs_in_portfolio: 10      # Portfolio diversification limit
  min_position_size: 0.05        # 5% minimum position
```

### 3. Run Analysis

```bash
# Full analysis
python main_updated.py

# Interactive mode with step-by-step prompts  
python main_updated.py --interactive

# Quick analysis (limited ETFs for testing)
python main_updated.py --quick
```

## 📈 Analysis Pipeline

### Step 1: Data Collection
- Discovers Round Hill ETF universe through web scraping
- Collects historical price data, dividend information, and fundamental metrics
- Validates data quality and completeness

### Step 2: ETF Analysis  
- **Performance Metrics**: Returns, volatility, Sharpe ratio, maximum drawdown
- **Dividend Analysis**: Yield, frequency, consistency, sustainability
- **Risk Assessment**: VaR, downside deviation, risk-adjusted returns
- **Technical Indicators**: Moving averages, RSI, trend analysis
- **Fundamental Metrics**: Assets under management, expense ratios, fund maturity

### Step 3: Portfolio Optimization
- **Modern Portfolio Theory**: Efficient frontier optimization
- **Strategy-Specific Optimization**:
  - Aggressive: Maximize Sharpe ratio with higher risk tolerance
  - Moderate: Target balanced risk-return profile  
  - Conservative: Minimize volatility with stable dividends
- **Constraint Handling**: Position limits, diversification requirements

### Step 4: Forecasting (12 Months)
- **Price Forecasting**: Machine learning models (Random Forest, Gradient Boosting)
- **Dividend Forecasting**: Growth projections and sustainability analysis
- **Economic Integration**: Fed policy, interest rates, market conditions
- **Scenario Analysis**: Bull, base, and bear case projections

### Step 5: Monte Carlo Risk Analysis
- **10,000+ Simulations**: Portfolio performance under various market conditions
- **Risk Metrics**: Value at Risk (VaR), Expected Shortfall, maximum drawdown
- **Stress Testing**: 2008 crisis, COVID-19, interest rate shocks
- **Confidence Intervals**: Statistical probability distributions

### Step 6: Visualization & Reporting
- **Interactive Dashboard**: Portfolio allocation, risk analysis, forecasts
- **Comprehensive Reports**: Executive summary, detailed metrics, recommendations
- **Export Formats**: HTML, PNG, PDF, JSON, Markdown

## 📊 Investment Strategies

### Aggressive Strategy
- **Focus**: Maximum dividend yield and growth potential
- **Risk Tolerance**: Higher volatility acceptable for returns
- **Portfolio**: 8-12 ETFs, up to 30% single position
- **Optimization**: Maximize Sharpe ratio

### Moderate Strategy
- **Focus**: Balanced risk-return with steady dividends
- **Risk Tolerance**: Moderate volatility, consistent income
- **Portfolio**: 6-8 ETFs, up to 25% single position
- **Optimization**: Target return with risk control

### Conservative Strategy
- **Focus**: Capital preservation with reliable dividends
- **Risk Tolerance**: Low volatility, defensive positioning
- **Portfolio**: 4-6 ETFs, up to 20% single position
- **Optimization**: Minimize volatility

## 🎯 Round Hill ETF Focus

This application specifically targets Round Hill Investments ETFs, known for:

- **Weekly Dividend ETFs**: Unique weekly payment schedules (WKLY)
- **Defensive Strategies**: Market-neutral and defensive income (DFND)  
- **Innovation Focus**: Technology and growth-oriented funds
- **Income Generation**: High-yield and covered call strategies

## 🔧 Key Technologies

- **Data Analysis**: pandas, numpy, scipy
- **Financial Analysis**: yfinance, pypfopt, cvxpy
- **Machine Learning**: scikit-learn, ensemble methods
- **Visualization**: plotly, matplotlib, seaborn
- **Web Scraping**: requests, beautifulsoup4
- **Risk Modeling**: Monte Carlo simulation, statistical analysis

## ⚠️ Risk Disclosure

This application is for educational and research purposes. All investments carry risk, and past performance does not guarantee future results. Users should:

- Conduct their own due diligence
- Consider their risk tolerance and investment objectives
- Consult with qualified financial advisors
- Understand that forecasts are estimates based on historical data

---

**Built for dividend income investors seeking data-driven portfolio optimization with comprehensive risk analysis.**
