# Trading Agent

An intelligent trading assistant that provides stock analysis and investment recommendations using AI-powered market research.

## Overview

This trading agent analyzes stocks and provides investment recommendations based on market data, news sentiment, and technical analysis following proven trading methodologies.

## Features

- **Stock Analysis**: Comprehensive evaluation of individual stocks and industry sectors
- **Investment Recommendations**: AI-powered suggestions for investment opportunities
- **Market Research**: Automated gathering of current news, market trends, and price data
- **Technical Analysis**: Integration of proven trading approaches including Dan Zanger methodology
- **Risk Assessment**: Detailed analysis including entry points, strike prices, and timing

## Architecture

The system follows a multi-stage processing pipeline:

1. **Query Processing**: User questions about stocks are analyzed by an LLM to extract intent and required information
2. **Data Aggregation**: The agent collects relevant market data including:
   - Current stock prices
   - Recent news and market sentiment
   - Industry trends and analysis
   - Historical performance data
3. **Analysis Engine**: All gathered information is processed by the LLM to determine investment strategies
4. **Response Generation**: Results are formatted and presented through the frontend interface
5. **Recommendation Display**: Buy/sell recommendations include detailed parameters:
   - Ticker symbol
   - Entry point
   - Strike price
   - Strike date
   - Risk metrics

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager
- API key for Anthropic Claude (for AI analysis)
- Internet connection for real-time market data

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TradingAgent
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

4. Run the application:
   
   ```bash
   python app.py
   ```
   
   Then open http://localhost:5001 in your browser

## Usage

### Web Interface

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your browser to `http://localhost:5001`

3. Ask questions about stocks, such as:
   - "What do you think about NVDA?"
   - "Should I invest in Tesla right now?"
   - "What are some good tech stocks to buy?"

### Error Handling

The system now includes robust data validation:
- **Data validation**: Checks if financial data is available before making AI analysis
- **Graceful failures**: If market data can't be retrieved, shows clear error instead of wasting AI tokens
- **Partial success**: If some symbols fail but others succeed, analysis continues with available data

### API Endpoints

**POST /api/chat**
- Submit a trading question for analysis
- Request body: `{"message": "Your stock question here"}`
- Response: Detailed analysis following Dan Zanger methodology

### Example Questions

- **Stock Analysis**: "What's your analysis of Apple stock?"
- **Market Opportunities**: "What are the best investment opportunities in AI stocks?"
- **Sector Analysis**: "How does the renewable energy sector look for investment?"
- **Risk Assessment**: "Is now a good time to buy growth stocks?"

## Contributing

I welcome contributions to improve the Trading Agent! Here's how you can help:

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where appropriate
- Write unit tests for new features

### Areas for Contribution

- Additional trading methodologies beyond Dan Zanger
- Enhanced market data sources
- Improved frontend UI/UX
- Mobile responsiveness
- Additional technical indicators
- Risk management features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **Important**: This trading agent is for educational and informational purposes only. It does not constitute financial advice. Always:

- Do your own research before making investment decisions
- Consult with qualified financial advisors
- Never invest more than you can afford to lose
- Understand that all investments carry risk
- Past performance does not guarantee future results

The developers are not responsible for any financial losses incurred from using this software.
    