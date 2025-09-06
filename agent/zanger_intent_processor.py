"""
Dan Zanger Intent Processor Service

A Python service module that processes user stock questions using Dan Zanger methodology
and creates structured research plans through Claude API integration.

Author: Claude
Date: 2025-08-23
"""

import json
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .financial_data import get_live_stock_data


@dataclass
class ZangerResearchPlan:
    """Structured data class for Zanger research plan output"""
    technical_pattern_analysis: List[str]
    volume_verification: List[str]
    zanger_fundamental_screen: List[str]
    sector_group_leadership: List[str]
    breakout_timing_signals: List[str]


@dataclass
class ZangerCriteriaChecklist:
    """Checklist for Dan Zanger methodology criteria"""
    technical_criteria: Dict[str, bool]
    fundamental_criteria: Dict[str, bool]
    risk_management: Dict[str, bool]
    entry_criteria: Dict[str, bool]


@dataclass
class OptionsOverlay:
    """Options trading overlay for Zanger methodology"""
    call_strategies: List[str]
    put_strategies: List[str]
    risk_defined_spreads: List[str]
    earnings_plays: List[str]


class ZangerIntentProcessor:
    """
    Dan Zanger Intent Processor for analyzing stock questions and creating research plans
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the processor with Claude API configuration
        
        Args:
            api_key: Anthropic API key. If None, expects ANTHROPIC_API_KEY environment variable
        """
        self.api_key = api_key or self._get_api_key()
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"
        self.max_retries = 3
        self.base_delay = 1.0
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _get_api_key(self) -> str:
        """Get API key from environment or .env file"""
        import os
        from dotenv import load_dotenv
        
        # Load .env file from project root (searches up directory tree)
        load_dotenv()
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or .env file")
        return api_key
    
    def _get_system_message(self) -> str:
        """
        Get the enhanced Dan Zanger system message with real-time data requirements
        
        Returns:
            System message string for Claude API
        """
        return """
You are a Dan Zanger trading methodology expert. You will be provided with LIVE market data fetched from real-time financial APIs.

Use ONLY the provided live market data for your analysis. Do not use any training data or make assumptions about current prices, volumes, or fundamentals.

Dan Zanger's Golden Rules & Methodology:

RISK MANAGEMENT:
- Never risk >1% of portfolio on single trade
- 8% Rule: Sell if stock falls 8% below purchase price, no exceptions
- Profit Taking: Sell half position after 20% gain from breakout, trail stop remainder
- Art of Concentration: Focus on fewer high-conviction stocks vs diversification

KEY SETUPS (verify with live data):
- Cup and Handle Formation: Long-term consolidation → breakout
- Flat Bases: Sideways tight range → volume breakout  
- Flags and Pennants: Short-term continuation patterns
- High Momentum Stocks: Explosive earnings, dominant sector position

VOLUME ANALYSIS (Zanger Volume Ratio):
- Breakouts need 50%+ above 20-day average volume
- Volume = institutional buying confirmation
- No breakout without volume confirmation

REQUIRED DATA LOOKUP: Before analysis, fetch current:
1. Stock price, 52-week range, technical patterns
2. Latest earnings growth, sector dominance
3. Volume vs 20-day average
4. Breakout levels and support/resistance

When screening multiple stocks, focus on the BEST Zanger setup found and provide detailed analysis for that one stock.

Response format (JSON only):

{
    "analysis_summary": "Brief analysis with key findings from live data",
    "symbols_analyzed": ["SYMBOL1"],
    "current_data": {
        "price": "$XXX.XX",
        "volume_vs_avg": "XXX%",
        "earnings_growth": "XX%",
        "sector_performance": "leading/lagging"
    },
    "zanger_analysis": {
        "pattern_type": "cup-and-handle/flat-base/flag/pennant/none",
        "volume_ratio": "XX% above 20-day avg",
        "breakout_level": "$XXX.XX",
        "meets_zanger_criteria": "pass/fail"
    },
    "recommendation": {
        "action": "BUY/SELL/HOLD/AVOID",
        "confidence": "high/medium/low",
        "reasoning": "Key factors supporting recommendation"
    },
    "trading_details": {
        "ticker": "SYMBOL",
        "entry_price": "$XXX.XX",
        "stop_loss": "$XXX.XX", 
        "target_price": "$XXX.XX",
        "position_size": "X% of portfolio",
        "time_horizon": "X weeks/months"
    },
    "risk_assessment": {
        "risk_level": "low/medium/high",
        "key_risks": ["risk1", "risk2"],
        "risk_reward_ratio": "X:1"
    }
}

Extract any stock symbols mentioned in the question. If no specific symbols, suggest 2-3 symbols that fit the current market environment and Zanger criteria. Ensure all JSON is properly formatted and valid.
"""
    
    def _extract_symbols_from_question(self, question: str) -> List[str]:
        """
        Extract potential stock symbols from user question using regex
        
        Args:
            question: User's question string
            
        Returns:
            List of potential stock symbols found
        """
        # Look for explicit stock symbols - either:
        # 1. Already uppercase words (like PLTR, AAPL)  
        # 2. Words preceded by $ (like $TSLA)
        
        symbols = []
        
        # Pattern 1: Find $SYMBOL format
        dollar_symbols = re.findall(r'\$([A-Za-z]{2,5})\b', question)
        symbols.extend([s.upper() for s in dollar_symbols])
        
        # Pattern 2: Find standalone uppercase words (but only if they look like tickers)
        # Only match if the word is in a context that suggests it's a ticker
        uppercase_pattern = r'\b[A-Z]{2,5}\b'
        potential_symbols = re.findall(uppercase_pattern, question)
        
        # Much more aggressive filtering - only include if it's likely a real ticker
        common_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 
            'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 
            'WHO', 'BOY', 'DID', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'WHAT', 'WILL', 'WITH', 'HAVE', 
            'FROM', 'THEY', 'KNOW', 'WANT', 'BEEN', 'GOOD', 'MUCH', 'SOME', 'TIME', 'VERY', 'WHEN', 'COME', 
            'HERE', 'JUST', 'LIKE', 'LONG', 'MAKE', 'MANY', 'OVER', 'SUCH', 'TAKE', 'THAN', 'THEM', 'WELL', 
            'WERE', 'BUYS', 'THEN', 'BEST', 'GOOD', 'WHAT', 'SOME', 'LOOK', 'NICE', 'THINK', 'ABOUT', 'STOCK',
            'STOCKS', 'BUY', 'SELL', 'HOLD', 'TRADE', 'INVEST', 'MARKET', 'PRICE', 'TODAY', 'ANALYSIS'
        }
        
        likely_tickers = [s for s in potential_symbols if s not in common_words and len(s) >= 2]
        symbols.extend(likely_tickers)
        
        # Remove duplicates
        return list(set(symbols))
    
    def _get_zanger_stock_suggestions(self, user_question: str) -> List[str]:
        """
        Get stock symbol suggestions from LLM based on current market conditions
        
        Args:
            user_question: User's original question
            
        Returns:
            List of suggested stock symbols
        """
        suggestion_prompt = f"""
The user asked: "{user_question}"

As a trading expert, suggest 3 stock ticker symbols that would be good candidates for Dan Zanger methodology analysis. Focus on well-known, actively traded stocks from strong sectors like technology, AI, healthcare, or energy.

Examples of the types of stocks that often meet Zanger criteria:
- Large cap tech stocks (AAPL, MSFT, NVDA, GOOGL)  
- Growth companies (TSLA, PLTR, AMZN, META)
- Healthcare leaders (JNJ, PFE, UNH)
- Financial stocks (JPM, BAC)

Just suggest 3 ticker symbols that would be worth analyzing. Respond with ONLY a JSON array:
["SYMBOL1", "SYMBOL2", "SYMBOL3"]
"""
        
        try:
            # Make a quick API call for suggestions
            headers = {
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
                'x-api-key': self.api_key
            }
            
            payload = {
                'model': self.model,
                'max_tokens': 100,
                'messages': [
                    {
                        'role': 'user',
                        'content': suggestion_prompt
                    }
                ]
            }
            
            response = self.session.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                api_response = response.json()
                content = api_response.get('content', [])
                if content and isinstance(content, list):
                    text_content = content[0].get('text', '')
                    
                    # Try to parse JSON from response
                    try:
                        suggestions = json.loads(text_content.strip())
                        if isinstance(suggestions, list):
                            return [s.upper() for s in suggestions if isinstance(s, str) and len(s) <= 5]
                    except:
                        # Fallback: extract symbols from text
                        symbols = re.findall(r'\b[A-Z]{2,5}\b', text_content)
                        return symbols[:3]
            
        except Exception as e:
            print(f"Error getting stock suggestions: {e}")
        
        return []  # Return empty if suggestions fail
    
    def _make_api_request(self, user_question: str) -> Dict[str, Any]:
        """
        Make API request to Claude with exponential backoff retry logic
        
        Args:
            user_question: The user's question to send to Claude
            
        Returns:
            API response dictionary
            
        Raises:
            Exception: If all retry attempts fail
        """
        headers = {
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'x-api-key': self.api_key
        }
        
        payload = {
            'model': self.model,
            'max_tokens': 4000,
            'system': self._get_system_message(),
            'messages': [
                {
                    'role': 'user',
                    'content': user_question
                }
            ]
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limit - wait longer
                    delay = self.base_delay * (2 ** attempt) * 2
                    time.sleep(delay)
                    continue
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise e
        
        if last_exception:
            raise last_exception
    
    def _parse_and_validate_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Claude API response and validate JSON structure
        
        Args:
            api_response: Raw API response from Claude
            
        Returns:
            Parsed and validated response dictionary
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract content from Claude response
            content = api_response.get('content', [])
            if not content or not isinstance(content, list):
                raise ValueError("Invalid API response format: no content found")
            
            # Get the text content
            text_content = content[0].get('text', '') if content else ''
            if not text_content:
                raise ValueError("Invalid API response format: no text content found")
            
            # Parse JSON from the response
            # Claude sometimes wraps JSON in markdown, so extract it
            json_match = re.search(r'```json\s*(.*?)\s*```', text_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object in the response
                json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = text_content
            
            # Parse JSON
            parsed_response = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                'analysis_summary',
                'symbols_analyzed',
                'current_data',
                'zanger_analysis',
                'recommendation',
                'trading_details',
                'risk_assessment'
            ]
            
            for field in required_fields:
                if field not in parsed_response:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate nested structures - more lenient for debugging
            recommendation = parsed_response.get('recommendation', {})
            trading_details = parsed_response.get('trading_details', {})
            
            if not recommendation.get('action'):
                raise ValueError("Missing recommendation action")
            
            # For debugging - show what we actually received
            if not trading_details.get('ticker'):
                raise ValueError(f"Missing trading ticker. Received trading_details: {trading_details}")
            
            return parsed_response
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in API response: {str(e)}")
        except KeyError as e:
            raise ValueError(f"Missing required field in API response: {str(e)}")
    
    def process_intent(self, user_question: str) -> Dict[str, Any]:
        """
        Main function to process user stock questions using Dan Zanger methodology
        
        Args:
            user_question: User's stock-related question
            
        Returns:
            Structured response dictionary with research plan and analysis
        """
        try:
            # Input validation
            if not user_question or not isinstance(user_question, str):
                return {
                    'error': 'Invalid input: user_question must be a non-empty string',
                    'success': False
                }
            
            if len(user_question.strip()) < 5:
                return {
                    'error': 'Invalid input: user_question too short',
                    'success': False
                }
            
            # Extract stock symbols and validate data availability
            symbols = self._extract_symbols_from_question(user_question)
            live_data = ""
            failed_symbols = []
            successful_symbols = []
            
            # If no specific symbols mentioned, check if user wants general recommendations
            # Check for various recommendation request patterns
            recommendation_keywords = ['good buys', 'recommendations', 'suggest', 'what to buy', 'best stocks', 'good buy', 'buys', 'stock picks', 'what stocks']
            is_recommendation_request = any(keyword in user_question.lower() for keyword in recommendation_keywords)
            
            if not symbols and is_recommendation_request:
                # First, ask LLM to suggest stocks based on current market conditions
                suggested_symbols = self._get_zanger_stock_suggestions(user_question)
                if suggested_symbols:
                    symbols = suggested_symbols[:3]  # Limit to 3 for efficiency
                    live_data += "\n--- ANALYZING ZANGER-CRITERIA STOCKS ---\n"
            
            if symbols:
                for symbol in symbols[:3]:  # Limit to 3 symbols to avoid API limits
                    try:
                        data_result = get_live_stock_data(symbol)
                        
                        if data_result.get("success"):
                            live_data += f"\n{data_result['data']}\n"
                            successful_symbols.append(symbol)
                        else:
                            failed_symbols.append({
                                "symbol": symbol,
                                "error": data_result.get("error", "Unknown error")
                            })
                            
                    except Exception as e:
                        failed_symbols.append({
                            "symbol": symbol,
                            "error": f"Unexpected error: {str(e)}"
                        })
            
            # Check if we have any usable market data
            if not live_data.strip() or (symbols and not successful_symbols):
                # No data available - don't make LLM call
                if failed_symbols:
                    # Specific symbols failed
                    if len(failed_symbols) == 1:
                        return {
                            'error': f'Could not retrieve data for {failed_symbols[0]["symbol"]}. Please check the symbol and try again.',
                            'success': False,
                            'data_fetch_failed': True
                        }
                    else:
                        failed_list = [f['symbol'] for f in failed_symbols]
                        return {
                            'error': f'Could not retrieve data for the requested stocks ({", ".join(failed_list)}). Please check the symbols and try again.',
                            'success': False,
                            'data_fetch_failed': True
                        }
                else:
                    # General question but no data available
                    return {
                        'error': 'Could not retrieve market data for analysis. Please specify a stock symbol (e.g., "What do you think about AAPL?") and try again.',
                        'success': False,
                        'data_fetch_failed': True
                    }
            
            # If some symbols failed but others succeeded, add warning to response
            partial_failure_warning = ""
            if failed_symbols:
                failed_list = [f['symbol'] for f in failed_symbols]
                partial_failure_warning = f"\n\nNote: Could not retrieve data for {', '.join(failed_list)}. Analysis is based on available data only."
            
            # Enhance user question with live data
            enhanced_question = f"""
USER QUESTION: {user_question}

LIVE MARKET DATA:
{live_data}

Based on the live market data provided above, analyze using Dan Zanger methodology:
"""
            
            # Make API request with enhanced question including live data
            api_response = self._make_api_request(enhanced_question)
            
            # Parse and validate response
            validated_response = self._parse_and_validate_response(api_response)
            
            # Add success flag and metadata
            validated_response['success'] = True
            validated_response['processed_at'] = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
            validated_response['methodology'] = 'Dan Zanger'
            
            # Add partial failure warning if applicable
            if partial_failure_warning:
                validated_response['data_warning'] = partial_failure_warning
            
            return validated_response
            
        except requests.exceptions.Timeout:
            return {
                'error': 'API request timed out - please try again',
                'success': False,
                'retry_recommended': True
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': f'API request failed: {str(e)}',
                'success': False,
                'retry_recommended': True
            }
        except ValueError as e:
            return {
                'error': f'Response parsing failed: {str(e)}',
                'success': False,
                'retry_recommended': False
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {str(e)}',
                'success': False,
                'retry_recommended': False
            }


def create_processor(api_key: Optional[str] = None) -> ZangerIntentProcessor:
    """
    Factory function to create ZangerIntentProcessor instance
    
    Args:
        api_key: Optional Anthropic API key
        
    Returns:
        Configured ZangerIntentProcessor instance
    """
    return ZangerIntentProcessor(api_key=api_key)


def process_intent(user_question: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to process user intent with Dan Zanger methodology
    
    Args:
        user_question: User's stock-related question
        api_key: Optional Anthropic API key
        
    Returns:
        Structured response dictionary with research plan and analysis
    """
    processor = create_processor(api_key)
    return processor.process_intent(user_question)

