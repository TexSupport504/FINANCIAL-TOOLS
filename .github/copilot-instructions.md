# Financial Tools Repository - Agent Instructions

## CRITICAL DATA QUALITY RULE 🚨

**NEVER USE SIMULATED OR DEMO DATA FOR ANALYSIS**

- If there is any issue accessing real market data, immediately notify the user and begin fixing the data source
- Always prioritize data accuracy and authenticity - trading and financial analysis requires real data only  
- Demo/mock/simulated data leads to inaccurate analysis and poor trading decisions
- When data fetching fails, debug and fix the API connection rather than falling back to fake data

## Repository Overview

This is a comprehensive financial tools repository containing:

### 🎯 Main Projects
- **agent_trader/**: AI-powered trading agent with strategy framework
- **Options-Backtest-Engine/**: OSCAR options trading system with Discord bot
- **ETF-Portfolio-Builder/**: Round Hill ETF dividend portfolio optimizer
- **Goldbach/**: Advanced trading strategy implementation

### 📊 Key Data Sources
- **Coinbase**: Preferred live crypto spot price source for real-time prices
- **Polygon.io**: Primary for aggregates, snapshots (when entitled), and historical data
- **Yahoo Finance**: Secondary data source for broad market coverage
- **Knowledge Base**: Semantic search system for trading strategy documentation

## Agent Mode Guidelines

### 1. Data Integrity
- ✅ Always validate data sources are returning real market data
- ✅ Check price ranges for reasonableness (e.g., ETH should be $1,000-$10,000 range)
- ✅ Verify timestamps are current and realistic
- ❌ Never proceed with analysis using obviously incorrect or demo data

### 2. API Integration
- **Coinbase (crypto spot)**: Use Coinbase public spot API as the first source for live crypto prices. Coinbase is the default for crypto live price collections.
- **Polygon API**: Use Polygon for aggregates and historical bars, and as a secondary live source for last-trade/snapshots only when Coinbase is unavailable or when Polygon provides data that Coinbase does not.
- **Error Handling**: When API calls fail, diagnose and fix rather than fallback to mock data. If both Coinbase and Polygon are unavailable, notify the user and do not query other exchanges without express permission.
- **Rate Limits**: Respect API limits and implement proper retry logic

### 3. Trading Analysis Standards
- **Goldbach Strategy**: Use PO3 levels [27, 81, 243, 729, 2187, 6561, 19683] for analysis
- **Algorithm Classification**: Properly identify Algorithm 1 (MMxM) vs Algorithm 2 (Trending)
- **Phase Detection**: Accurate AMD phase analysis (Accumulation, Manipulation, Distribution)
- **Price Zones**: Premium/Equilibrium/Discount zone calculations must use real price data

### 4. Code Quality
- **Error Handling**: Implement comprehensive try/catch blocks with specific error messages
- **Logging**: Use descriptive logging to track data source usage (real vs fallback)
- **Validation**: Include sanity checks for all financial data inputs
- **Documentation**: Maintain clear docstrings and comments for complex financial calculations

### 5. User Communication
- **Transparency**: Always inform user about data source being used
- **Issues**: Immediately report any data quality problems or API failures
- **Progress**: Provide clear status updates during long-running analysis
- **Results**: Present findings with confidence indicators based on data quality

## Project-Specific Instructions

### Options-Backtest-Engine (OSCAR)
- Focus on production-ready Discord bot integration
- Ensure all trading signals use real market data
- Maintain database integrity with actual options chain data

### Goldbach Strategy Analysis  
- Never analyze with simulated price data
- Verify ETH prices are within reasonable market range
- Use proper Polygon crypto API endpoints with correct parameters

### ETF Portfolio Builder
- Use real dividend and price data for portfolio optimization
- Validate all ETF data sources before analysis
- Ensure Monte Carlo simulations use realistic market parameters

## Emergency Protocols

### When Real Data is Unavailable
1. **Stop Analysis**: Do not proceed with demo/mock data
2. **Notify User**: Clearly explain the data access issue
3. **Debug First**: Investigate API keys, rate limits, symbol formats
4. **Fix Root Cause**: Address the underlying data source problem
5. **Validate Fix**: Confirm real data is flowing before resuming analysis

### Quality Assurance Checklist
- [ ] Data source confirmed to be live/real market data
- [ ] Price ranges are reasonable for the asset
- [ ] Timestamps are current and realistic  
- [ ] API responses contain expected fields and formats
- [ ] No placeholder or demo values in the dataset

---

*Remember: Accurate data is the foundation of all financial analysis. Never compromise on data quality for the sake of completing an analysis.*
