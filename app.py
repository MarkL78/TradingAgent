from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import agent.zanger_intent_processor as zp
import os
import anthropic

app = Flask(__name__)
CORS(app)

# Store API key per session (in production, use proper session management)
active_api_keys = {}

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('frontend', filename)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        api_key = data.get('apiKey', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not api_key.startswith('sk-ant-api'):
            return jsonify({'error': 'Invalid API key format'}), 400
        
        # Test the API key by making a simple request
        try:
            client = anthropic.Anthropic(api_key=api_key)
            # Test with a minimal request
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            # Store the API key for this session
            session_id = request.remote_addr  # Simple session ID based on IP
            active_api_keys[session_id] = api_key
            
            return jsonify({'success': True, 'message': 'API key validated successfully'})
            
        except Exception as e:
            return jsonify({'error': 'Invalid API key or authentication failed'}), 401
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        session_id = request.remote_addr
        api_key = active_api_keys.get(session_id)
        
        if not api_key:
            return jsonify({'error': 'Not authenticated. Please login first.'}), 401
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Set the API key for this request
        os.environ['ANTHROPIC_API_KEY'] = api_key
        
        # Process with enhanced Zanger methodology
        result = zp.process_intent(user_message)
        
        if not result.get('success', False):
            return jsonify({'error': result.get('error', 'Analysis failed')}), 500
        
        return jsonify({
            'success': True,
            'analysis': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    try:
        session_id = request.remote_addr
        api_key = active_api_keys.get(session_id)
        
        if not api_key:
            return jsonify({'error': 'Not authenticated. Please login first.'}), 401
        
        data = request.get_json()
        symbol = data.get('symbol', '').strip().upper()
        
        if not symbol:
            return jsonify({'error': 'Stock symbol is required'}), 400
        
        # Import and use the financial data service
        from agent.financial_data import FinancialDataService
        service = FinancialDataService()
        stock_data = service.get_stock_data(symbol)
        
        if 'error' in stock_data:
            return jsonify({'success': False, 'error': stock_data['error']}), 400
        
        return jsonify({
            'success': True,
            'data': stock_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session_id = request.remote_addr
        if session_id in active_api_keys:
            del active_api_keys[session_id]
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)