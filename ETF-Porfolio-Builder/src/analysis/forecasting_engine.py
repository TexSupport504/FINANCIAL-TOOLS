"""
Forecasting Engine - Predicts ETF performance and portfolio returns over 12 months
Incorporates economic indicators, Fed policy, and market conditions
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class ForecastingEngine:
    """Advanced forecasting engine for ETF performance prediction"""
    
    def __init__(self, config):
        self.config = config
        self.forecast_horizon = config['forecasting']['forecast_horizon_months']
        self.confidence_levels = config['forecasting']['confidence_levels']
        self.economic_indicators = self._initialize_economic_indicators()
        
    def generate_forecasts(self, etf_data, etf_metrics, economic_data=None):
        """
        Generate comprehensive 12-month forecasts for all ETFs
        """
        logger.info(f"Generating {self.forecast_horizon}-month forecasts for {len(etf_data)} ETFs")
        
        forecasts = {}
        
        for symbol, data in etf_data.items():
            try:
                etf_forecast = self._forecast_single_etf(symbol, data, etf_metrics.get(symbol, {}), economic_data)
                forecasts[symbol] = etf_forecast
                logger.debug(f"✅ Forecast complete for {symbol}")
            except Exception as e:
                logger.error(f"Forecast failed for {symbol}: {e}")
                forecasts[symbol] = self._empty_forecast(symbol)
        
        # Generate market environment forecast
        market_forecast = self._forecast_market_environment(economic_data)
        
        logger.info(f"Forecasting completed for {len(forecasts)} ETFs")
        
        return {
            'etf_forecasts': forecasts,
            'market_forecast': market_forecast,
            'forecast_date': datetime.now(),
            'horizon_months': self.forecast_horizon
        }
    
    def _forecast_single_etf(self, symbol, etf_data, etf_metrics, economic_data):
        """Generate comprehensive forecast for a single ETF"""
        
        hist_data = etf_data['historical_data']
        
        if hist_data.empty or len(hist_data) < 60:
            return self._empty_forecast(symbol)
        
        # Prepare features for forecasting
        features_df = self._prepare_forecasting_features(hist_data, etf_metrics, economic_data)
        
        # Price forecast
        price_forecast = self._forecast_prices(features_df, hist_data['Close'])
        
        # Dividend forecast
        dividend_forecast = self._forecast_dividends(etf_metrics.get('dividend_metrics', {}))
        
        # Risk forecast
        risk_forecast = self._forecast_risk_metrics(hist_data['Returns'])
        
        # Technical forecast
        technical_forecast = self._forecast_technical_indicators(hist_data)
        
        return {
            'symbol': symbol,
            'price_forecast': price_forecast,
            'dividend_forecast': dividend_forecast,
            'risk_forecast': risk_forecast,
            'technical_forecast': technical_forecast,
            'total_return_forecast': self._calculate_total_return_forecast(price_forecast, dividend_forecast),
            'forecast_confidence': self._calculate_forecast_confidence(features_df, hist_data),
            'scenario_analysis': self._generate_scenario_analysis(price_forecast, dividend_forecast)
        }
    
    def _prepare_forecasting_features(self, hist_data, etf_metrics, economic_data):
        """Prepare comprehensive feature set for forecasting"""
        
        # Technical features
        features = pd.DataFrame(index=hist_data.index)
        
        # Price-based features
        features['returns'] = hist_data['Returns']
        features['volatility'] = hist_data['Returns'].rolling(20).std()
        features['momentum_5d'] = hist_data['Close'].pct_change(5)
        features['momentum_20d'] = hist_data['Close'].pct_change(20)
        features['rsi'] = self._calculate_rsi(hist_data['Close'])
        
        # Moving averages
        features['sma_ratio_50'] = hist_data['Close'] / hist_data['Close'].rolling(50).mean()
        features['sma_ratio_200'] = hist_data['Close'] / hist_data['Close'].rolling(200).mean()
        
        # Volume features (if available)
        if 'Volume' in hist_data.columns:
            features['volume_ratio'] = hist_data['Volume'] / hist_data['Volume'].rolling(20).mean()
        else:
            features['volume_ratio'] = 1.0
        
        # Seasonal features
        features['month'] = features.index.month
        features['quarter'] = features.index.quarter
        features['day_of_week'] = features.index.dayofweek
        
        # Economic indicators (simplified - would integrate real data)
        features['fed_rate'] = self.economic_indicators['fed_funds_rate']
        features['vix_level'] = self.economic_indicators['vix_level']
        features['yield_curve'] = self.economic_indicators['yield_curve_slope']
        
        # Dividend-specific features
        dividend_yield = etf_metrics.get('dividend_metrics', {}).get('dividend_yield', 0.04)
        features['dividend_yield'] = dividend_yield
        features['yield_spread'] = dividend_yield - self.economic_indicators['fed_funds_rate']
        
        return features.dropna()
    
    def _forecast_prices(self, features_df, price_series):
        """Forecast price movements using machine learning"""
        
        if len(features_df) < 60:
            return self._simple_price_forecast(price_series)
        
        # Prepare target variable (future returns)
        target_days = 21  # Forecast 21 trading days ahead
        features_df = features_df.copy()
        features_df['target'] = features_df['returns'].shift(-target_days)
        
        # Remove NaN values
        model_data = features_df.dropna()
        
        if len(model_data) < 30:
            return self._simple_price_forecast(price_series)
        
        # Features and target
        feature_columns = [col for col in model_data.columns if col != 'target']
        X = model_data[feature_columns]
        y = model_data['target']
        
        try:
            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=3)
            
            # Train ensemble models
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            
            # Fit models
            rf_model.fit(X, y)
            gb_model.fit(X, y)
            
            # Generate forecasts
            current_features = X.iloc[-1:].values
            
            # Ensemble prediction
            rf_pred = rf_model.predict(current_features)[0]
            gb_pred = gb_model.predict(current_features)[0]
            ensemble_pred = (rf_pred + gb_pred) / 2
            
            # Generate monthly forecasts
            current_price = price_series.iloc[-1]
            monthly_forecasts = []
            
            for month in range(1, self.forecast_horizon + 1):
                # Monthly return prediction with decay
                monthly_return = ensemble_pred * (1 - 0.05 * month)  # Decay factor
                forecasted_price = current_price * (1 + monthly_return * month / target_days * 21)
                
                monthly_forecasts.append({
                    'month': month,
                    'price': forecasted_price,
                    'return': monthly_return,
                    'confidence': max(0.5, 0.8 - 0.05 * month)  # Decreasing confidence
                })
            
            return {
                'method': 'machine_learning',
                'monthly_forecasts': monthly_forecasts,
                'model_performance': {
                    'rf_score': rf_model.score(X, y),
                    'gb_score': gb_model.score(X, y)
                }
            }
            
        except Exception as e:
            logger.warning(f"ML price forecast failed: {e}. Using simple forecast.")
            return self._simple_price_forecast(price_series)
    
    def _simple_price_forecast(self, price_series):
        """Simple price forecast based on historical trends"""
        
        if len(price_series) < 20:
            # Very basic forecast
            monthly_forecasts = []
            current_price = price_series.iloc[-1] if not price_series.empty else 50
            
            for month in range(1, self.forecast_horizon + 1):
                monthly_forecasts.append({
                    'month': month,
                    'price': current_price * (1 + 0.005 * month),  # 0.5% monthly growth
                    'return': 0.005,
                    'confidence': 0.3
                })
            
            return {
                'method': 'basic_trend',
                'monthly_forecasts': monthly_forecasts,
                'model_performance': {'score': 0.0}
            }
        
        # Calculate trend and seasonality
        returns = price_series.pct_change().dropna()
        avg_return = returns.mean()
        volatility = returns.std()
        
        current_price = price_series.iloc[-1]
        monthly_forecasts = []
        
        for month in range(1, self.forecast_horizon + 1):
            # Add some random walk with drift
            monthly_return = avg_return * 21 + np.random.normal(0, volatility * np.sqrt(21)) * 0.1
            forecasted_price = current_price * ((1 + avg_return) ** (month * 21))
            
            monthly_forecasts.append({
                'month': month,
                'price': forecasted_price,
                'return': monthly_return,
                'confidence': max(0.4, 0.7 - 0.03 * month)
            })
        
        return {
            'method': 'trend_based',
            'monthly_forecasts': monthly_forecasts,
            'model_performance': {'trend': avg_return, 'volatility': volatility}
        }
    
    def _forecast_dividends(self, dividend_metrics):
        """Forecast dividend payments and yield changes"""
        
        current_yield = dividend_metrics.get('dividend_yield', 0.04)
        dividend_frequency = dividend_metrics.get('dividend_frequency', 'Unknown')
        growth_rate = dividend_metrics.get('dividend_growth_rate', 0.0)
        is_weekly = dividend_metrics.get('is_weekly_dividend', False)
        
        # Forecast dividend sustainability
        sustainability_score = dividend_metrics.get('dividend_consistency', 0.7)
        
        dividend_forecasts = []
        
        for month in range(1, self.forecast_horizon + 1):
            # Project dividend growth
            projected_yield = current_yield * (1 + growth_rate / 12) ** month
            
            # Account for economic environment impact
            fed_rate_impact = -0.1 * (self.economic_indicators['fed_funds_rate'] - 0.02)  # Rate sensitivity
            adjusted_yield = projected_yield + fed_rate_impact
            
            # Calculate expected dividend payments
            if is_weekly:
                payments_per_month = 4.33  # ~4.33 weeks per month
            elif dividend_frequency == 'Monthly':
                payments_per_month = 1
            elif dividend_frequency == 'Quarterly':
                payments_per_month = 1/3
            else:
                payments_per_month = 1/12  # Annual
            
            dividend_forecasts.append({
                'month': month,
                'projected_yield': adjusted_yield,
                'payments_in_month': payments_per_month,
                'sustainability_score': sustainability_score * (1 - 0.01 * month),  # Slight decay
                'dividend_confidence': min(0.8, sustainability_score + 0.1)
            })
        
        return {
            'current_yield': current_yield,
            'is_weekly_dividend': is_weekly,
            'growth_rate': growth_rate,
            'monthly_forecasts': dividend_forecasts,
            'sustainability_outlook': 'Strong' if sustainability_score > 0.7 else 'Moderate' if sustainability_score > 0.5 else 'Weak'
        }
    
    def _forecast_risk_metrics(self, returns_series):
        """Forecast volatility and risk metrics"""
        
        if returns_series.empty or len(returns_series) < 30:
            return {
                'volatility_forecast': [0.15] * self.forecast_horizon,
                'var_forecast': [-0.02] * self.forecast_horizon,
                'risk_outlook': 'Unknown'
            }
        
        # Calculate current volatility
        current_vol = returns_series.rolling(30).std().iloc[-1] * np.sqrt(252)
        
        # GARCH-like volatility forecasting (simplified)
        vol_forecasts = []
        vol_persistence = 0.85  # Volatility persistence factor
        
        for month in range(1, self.forecast_horizon + 1):
            # Volatility mean reversion
            long_term_vol = returns_series.std() * np.sqrt(252)
            forecasted_vol = long_term_vol + (current_vol - long_term_vol) * (vol_persistence ** month)
            vol_forecasts.append(forecasted_vol)
        
        # VaR forecasts
        var_forecasts = [-1.645 * vol / np.sqrt(252) for vol in vol_forecasts]  # 95% daily VaR
        
        # Risk outlook
        avg_forecast_vol = np.mean(vol_forecasts)
        if avg_forecast_vol < 0.15:
            risk_outlook = 'Low'
        elif avg_forecast_vol < 0.25:
            risk_outlook = 'Moderate'
        else:
            risk_outlook = 'High'
        
        return {
            'volatility_forecast': vol_forecasts,
            'var_forecast': var_forecasts,
            'risk_outlook': risk_outlook,
            'current_volatility': current_vol
        }
    
    def _forecast_technical_indicators(self, hist_data):
        """Forecast technical indicator trends"""
        
        if hist_data.empty:
            return {'trend_forecast': 'Neutral', 'momentum_score': 0}
        
        current_price = hist_data['Close'].iloc[-1]
        
        # Calculate current technical state
        sma_50 = hist_data['Close'].rolling(50).mean().iloc[-1]
        sma_200 = hist_data['Close'].rolling(200).mean().iloc[-1]
        
        # Trend analysis
        if current_price > sma_50 > sma_200:
            trend_forecast = 'Bullish'
            momentum_score = 0.8
        elif current_price > sma_50 and sma_50 < sma_200:
            trend_forecast = 'Mixed'
            momentum_score = 0.3
        elif current_price < sma_50 < sma_200:
            trend_forecast = 'Bearish'
            momentum_score = -0.8
        else:
            trend_forecast = 'Neutral'
            momentum_score = 0
        
        return {
            'trend_forecast': trend_forecast,
            'momentum_score': momentum_score,
            'support_level': min(sma_50, sma_200),
            'resistance_level': max(current_price * 1.1, sma_50 * 1.05)
        }
    
    def _calculate_total_return_forecast(self, price_forecast, dividend_forecast):
        """Calculate total return combining price appreciation and dividends"""
        
        total_returns = []
        
        price_forecasts = price_forecast['monthly_forecasts']
        dividend_forecasts = dividend_forecast['monthly_forecasts']
        
        for month in range(self.forecast_horizon):
            price_component = price_forecasts[month]['return'] if month < len(price_forecasts) else 0
            dividend_component = dividend_forecasts[month]['projected_yield'] / 12 if month < len(dividend_forecasts) else 0
            
            total_return = price_component + dividend_component
            
            total_returns.append({
                'month': month + 1,
                'price_return': price_component,
                'dividend_return': dividend_component,
                'total_return': total_return,
                'cumulative_return': sum(tr['total_return'] for tr in total_returns) + total_return
            })
        
        return total_returns
    
    def _calculate_forecast_confidence(self, features_df, hist_data):
        """Calculate overall confidence in forecasts"""
        
        # Data quality factors
        data_length_score = min(len(hist_data) / 252, 1.0)  # 1 year of data = max score
        data_completeness = 1 - features_df.isnull().mean().mean()
        
        # Market environment stability
        volatility_score = 1 - min(hist_data['Returns'].std() / 0.03, 1.0)  # Lower volatility = higher confidence
        
        # Overall confidence
        confidence = (data_length_score * 0.4 + data_completeness * 0.3 + volatility_score * 0.3)
        
        return {
            'overall_confidence': confidence,
            'data_quality': data_length_score,
            'completeness': data_completeness,
            'stability': volatility_score
        }
    
    def _generate_scenario_analysis(self, price_forecast, dividend_forecast):
        """Generate bull, base, and bear case scenarios"""
        
        base_case = price_forecast['monthly_forecasts'][-1] if price_forecast['monthly_forecasts'] else {'return': 0}
        base_return = base_case.get('return', 0)
        
        scenarios = {
            'bull_case': {
                'annual_return': base_return * 1.5,
                'probability': 0.25,
                'description': 'Favorable market conditions, strong dividend growth'
            },
            'base_case': {
                'annual_return': base_return,
                'probability': 0.50,
                'description': 'Expected scenario based on current trends'
            },
            'bear_case': {
                'annual_return': base_return * 0.3,
                'probability': 0.25,
                'description': 'Market stress, dividend cuts possible'
            }
        }
        
        return scenarios
    
    def _forecast_market_environment(self, economic_data):
        """Forecast overall market environment"""
        
        # Economic outlook (simplified)
        fed_outlook = self._analyze_fed_policy()
        market_sentiment = self._analyze_market_sentiment()
        dividend_environment = self._analyze_dividend_environment()
        
        return {
            'fed_policy_outlook': fed_outlook,
            'market_sentiment': market_sentiment,
            'dividend_environment': dividend_environment,
            'overall_outlook': 'Positive' if fed_outlook == 'Dovish' and market_sentiment > 0.5 else 'Neutral'
        }
    
    def _initialize_economic_indicators(self):
        """Initialize economic indicators (would connect to real data sources)"""
        return {
            'fed_funds_rate': 0.025,  # Current Fed funds rate
            'vix_level': 20.0,       # VIX level
            'yield_curve_slope': 0.02, # 10Y - 2Y yield spread
            'inflation_rate': 0.03,   # Current inflation
            'gdp_growth': 0.025      # GDP growth rate
        }
    
    def _analyze_fed_policy(self):
        """Analyze Federal Reserve policy outlook"""
        # Simplified analysis
        if self.economic_indicators['fed_funds_rate'] < 0.03:
            return 'Dovish'
        elif self.economic_indicators['fed_funds_rate'] > 0.05:
            return 'Hawkish'
        else:
            return 'Neutral'
    
    def _analyze_market_sentiment(self):
        """Analyze market sentiment indicators"""
        # VIX-based sentiment (simplified)
        vix = self.economic_indicators['vix_level']
        if vix < 15:
            return 0.8  # Bullish
        elif vix < 25:
            return 0.5  # Neutral
        else:
            return 0.2  # Bearish
    
    def _analyze_dividend_environment(self):
        """Analyze dividend investment environment"""
        # Based on yield curve and Fed policy
        yield_spread = self.economic_indicators['yield_curve_slope']
        fed_rate = self.economic_indicators['fed_funds_rate']
        
        if yield_spread > 0.015 and fed_rate < 0.04:
            return 'Favorable'
        elif yield_spread < 0:
            return 'Challenging'
        else:
            return 'Neutral'
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI for technical analysis"""
        if len(prices) < period + 1:
            return pd.Series([50] * len(prices), index=prices.index)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    def _empty_forecast(self, symbol):
        """Return empty forecast structure"""
        return {
            'symbol': symbol,
            'price_forecast': {'method': 'insufficient_data', 'monthly_forecasts': []},
            'dividend_forecast': {'current_yield': 0, 'monthly_forecasts': []},
            'risk_forecast': {'volatility_forecast': [], 'risk_outlook': 'Unknown'},
            'technical_forecast': {'trend_forecast': 'Neutral', 'momentum_score': 0},
            'total_return_forecast': [],
            'forecast_confidence': {'overall_confidence': 0},
            'scenario_analysis': {}
        }
