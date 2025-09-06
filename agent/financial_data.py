"""
Financial Data Service
Fetches real-time stock data using yfinance and other free APIs
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time


class FinancialDataService:
    """Service to fetch real-time financial data with caching"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Simple in-memory cache with 15-minute TTL
        self.cache = {}
        self.cache_ttl = 900  # 15 minutes in seconds
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache:
            return False
        
        cache_time = self.cache[symbol].get('cached_at', 0)
        return time.time() - cache_time < self.cache_ttl
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive stock data for a symbol with caching
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Dictionary with current price, volume, earnings, etc.
        """
        # Check cache first
        if self._is_cache_valid(symbol):
            cached_data = self.cache[symbol].copy()
            cached_data.pop('cached_at', None)  # Remove cache metadata
            cached_data['from_cache'] = True
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get recent price data (last 30 days for volume analysis)
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                return {"error": f"No data available for {symbol}"}
            
            current_price = hist['Close'].iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            avg_volume_20d = hist['Volume'].tail(20).mean()
            
            # Calculate 52-week range
            year_hist = ticker.history(period="1y")
            week_52_high = year_hist['High'].max() if not year_hist.empty else None
            week_52_low = year_hist['Low'].min() if not year_hist.empty else None
            
            # Volume ratio
            volume_ratio = (current_volume / avg_volume_20d * 100) if avg_volume_20d > 0 else 0
            
            # Get quarterly EPS
            quarterly_eps = None
            try:
                quarterly_financials = ticker.quarterly_financials
                if not quarterly_financials.empty and 'Net Income' in quarterly_financials.index:
                    # Get shares outstanding
                    shares = info.get('sharesOutstanding')
                    if shares:
                        latest_net_income = quarterly_financials.loc['Net Income'].iloc[0]
                        quarterly_eps = round((latest_net_income / shares), 2)
            except:
                # Fallback to basic EPS from info
                quarterly_eps = info.get('trailingEps')
            
            stock_data = {
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "volume": int(current_volume),
                "avg_volume_20d": int(avg_volume_20d),
                "volume_ratio_pct": round(volume_ratio, 1),
                "52_week_high": round(week_52_high, 2) if week_52_high else None,
                "52_week_low": round(week_52_low, 2) if week_52_low else None,
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "quarterly_eps": quarterly_eps,
                "earnings_growth": info.get('earningsGrowth'),
                "revenue_growth": info.get('revenueGrowth'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "from_cache": False
            }
            
            # Cache the data
            cache_data = stock_data.copy()
            cache_data['cached_at'] = time.time()
            self.cache[symbol] = cache_data
            
            return stock_data
            
        except Exception as e:
            return {"error": f"Failed to fetch data for {symbol}: {str(e)}"}
    
    def get_earnings_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest earnings data for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Use income statement instead of deprecated earnings
            try:
                income_stmt = ticker.quarterly_income_stmt
                if income_stmt is not None and not income_stmt.empty and 'Net Income' in income_stmt.index:
                    net_income_data = income_stmt.loc['Net Income'].dropna()
                    if len(net_income_data) >= 2:
                        latest_earnings = net_income_data.iloc[0] / 1e9  # Convert to billions
                        prev_earnings = net_income_data.iloc[1] / 1e9
                        
                        earnings_growth = None
                        if prev_earnings != 0:
                            earnings_growth = ((latest_earnings - prev_earnings) / abs(prev_earnings)) * 100
                        
                        return {
                            "latest_earnings": round(latest_earnings, 2),
                            "earnings_growth_yoy": round(earnings_growth, 1) if earnings_growth else None,
                            "earnings_date": net_income_data.index[0].strftime("%Y-%m-%d") if hasattr(net_income_data.index[0], 'strftime') else "Recent"
                        }
            except:
                pass
            
            # Fallback to basic info
            info = ticker.info
            return {
                "latest_earnings": info.get('trailingEps'),
                "earnings_growth_yoy": round(info.get('earningsGrowth', 0) * 100, 1) if info.get('earningsGrowth') else None,
                "earnings_date": "Recent"
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch earnings for {symbol}: {str(e)}"}
    
    def validate_data_available(self, symbol: str) -> Dict[str, Any]:
        """
        Check if we can get valid financial data for a symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with validation result and data if available
        """
        stock_data = self.get_stock_data(symbol)
        
        if "error" in stock_data:
            return {
                "success": False,
                "error": stock_data["error"],
                "symbol": symbol
            }
        
        # Check if we have essential data
        essential_fields = ['current_price', 'volume', 'avg_volume_20d']
        missing_fields = [field for field in essential_fields if stock_data.get(field) is None]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing essential data for {symbol}: {', '.join(missing_fields)}",
                "symbol": symbol
            }
        
        return {
            "success": True,
            "data": stock_data,
            "symbol": symbol
        }
    
    def format_for_llm(self, symbol: str) -> Dict[str, Any]:
        """
        Get formatted stock data for LLM consumption
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with success status and formatted data or error
        """
        validation_result = self.validate_data_available(symbol)
        
        if not validation_result["success"]:
            return {
                "success": False,
                "error": validation_result["error"],
                "symbol": symbol
            }
        
        stock_data = validation_result["data"]
        earnings_data = self.get_earnings_data(symbol)
        
        # Format the data
        formatted_data = f"""
LIVE MARKET DATA FOR {symbol} (Updated: {stock_data['last_updated']}):

PRICE DATA:
- Current Price: ${stock_data['current_price']}
- 52-Week Range: ${stock_data['52_week_low']} - ${stock_data['52_week_high']}

VOLUME ANALYSIS:
- Current Volume: {stock_data['volume']:,}
- 20-Day Average Volume: {stock_data['avg_volume_20d']:,}
- Volume Ratio: {stock_data['volume_ratio_pct']}% of 20-day average

FUNDAMENTAL DATA:
- Market Cap: ${stock_data['market_cap']:,} if stock_data['market_cap'] else 'N/A'
- P/E Ratio: {stock_data['pe_ratio']} if stock_data['pe_ratio'] else 'N/A'
- Sector: {stock_data['sector'] or 'N/A'}
- Industry: {stock_data['industry'] or 'N/A'}

EARNINGS DATA:
- Latest Earnings: ${earnings_data.get('latest_earnings', 'N/A')} per share
- YoY Earnings Growth: {earnings_data.get('earnings_growth_yoy', 'N/A')}%
- Last Earnings Date: {earnings_data.get('earnings_date', 'N/A')}
"""
        
        return {
            "success": True,
            "data": formatted_data.strip(),
            "symbol": symbol
        }


def get_live_stock_data(symbol: str) -> Dict[str, Any]:
    """
    Convenience function to get formatted stock data
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with success status and data or error
    """
    service = FinancialDataService()
    return service.format_for_llm(symbol)


if __name__ == "__main__":
    # Test the service
    service = FinancialDataService()
    print(service.format_for_llm("AAPL"))