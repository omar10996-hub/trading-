"""
Servidor API intermediario para conectar GPT personalizado con Alpaca
Este servidor expone endpoints seguros que tu GPT puede llamar

Autor: Manus AI
Fecha: 23 de octubre de 2025
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import alpaca_trade_api as tradeapi
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permitir llamadas desde el GPT

# Configuración de Alpaca (usando variables de entorno por seguridad)
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', 'TU_ALPACA_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', 'TU_ALPACA_SECRET')
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'

# Inicializar cliente de Alpaca
alpaca = tradeapi.REST(
    key_id=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
    base_url=ALPACA_BASE_URL,
    api_version='v2'
)

@app.route('/', methods=['GET'])
def home():
    """Página de inicio con información de la API"""
    return jsonify({
        'service': 'Trading API Server',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'stock_price': '/api/stock/price/<symbol>',
            'stock_bars': '/api/stock/bars/<symbol>',
            'account': '/api/account',
            'positions': '/api/positions',
            'orders': '/api/orders',
            'market_status': '/api/market/status'
        }
    })

@app.route('/api/stock/price/<symbol>', methods=['GET'])
def get_stock_price(symbol):
    """
    Obtiene el precio actual de una acción
    Ejemplo: GET /api/stock/price/AAPL
    """
    try:
        # Obtener última cotización
        quote = alpaca.get_latest_trade(symbol)
        
        return jsonify({
            'symbol': symbol.upper(),
            'price': float(quote.price),
            'timestamp': quote.timestamp.isoformat(),
            'size': int(quote.size),
            'exchange': quote.exchange
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stock/quote/<symbol>', methods=['GET'])
def get_stock_quote(symbol):
    """
    Obtiene la cotización completa (bid/ask) de una acción
    Ejemplo: GET /api/stock/quote/AAPL
    """
    try:
        quote = alpaca.get_latest_quote(symbol)
        
        return jsonify({
            'symbol': symbol.upper(),
            'bid_price': float(quote.bid_price),
            'bid_size': int(quote.bid_size),
            'ask_price': float(quote.ask_price),
            'ask_size': int(quote.ask_size),
            'timestamp': quote.timestamp.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stock/bars/<symbol>', methods=['GET'])
def get_stock_bars(symbol):
    """
    Obtiene datos históricos de una acción
    Ejemplo: GET /api/stock/bars/AAPL?timeframe=1Hour&limit=10
    
    Parámetros:
    - timeframe: 1Min, 5Min, 15Min, 1Hour, 1Day (default: 1Hour)
    - limit: número de barras (default: 10, max: 100)
    """
    try:
        timeframe = request.args.get('timeframe', '1Hour')
        limit = min(int(request.args.get('limit', 10)), 100)
        
        bars = alpaca.get_bars(symbol, timeframe, limit=limit).df
        
        # Convertir a formato JSON amigable
        data = []
        for index, row in bars.iterrows():
            data.append({
                'timestamp': index.isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        
        return jsonify({
            'symbol': symbol.upper(),
            'timeframe': timeframe,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/account', methods=['GET'])
def get_account():
    """
    Obtiene información de la cuenta
    Ejemplo: GET /api/account
    """
    try:
        account = alpaca.get_account()
        
        return jsonify({
            'account_number': account.account_number,
            'status': account.status,
            'currency': account.currency,
            'cash': float(account.cash),
            'portfolio_value': float(account.portfolio_value),
            'buying_power': float(account.buying_power),
            'equity': float(account.equity),
            'last_equity': float(account.last_equity),
            'pattern_day_trader': account.pattern_day_trader,
            'trading_blocked': account.trading_blocked,
            'transfers_blocked': account.transfers_blocked,
            'account_blocked': account.account_blocked
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """
    Obtiene todas las posiciones abiertas
    Ejemplo: GET /api/positions
    """
    try:
        positions = alpaca.list_positions()
        
        result = []
        for position in positions:
            result.append({
                'symbol': position.symbol,
                'qty': float(position.qty),
                'side': position.side,
                'avg_entry_price': float(position.avg_entry_price),
                'current_price': float(position.current_price),
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc) * 100,  # Convertir a porcentaje
                'unrealized_intraday_pl': float(position.unrealized_intraday_pl),
                'unrealized_intraday_plpc': float(position.unrealized_intraday_plpc) * 100
            })
        
        return jsonify({
            'count': len(result),
            'positions': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/positions/<symbol>', methods=['GET'])
def get_position(symbol):
    """
    Obtiene una posición específica
    Ejemplo: GET /api/positions/AAPL
    """
    try:
        position = alpaca.get_position(symbol)
        
        return jsonify({
            'symbol': position.symbol,
            'qty': float(position.qty),
            'side': position.side,
            'avg_entry_price': float(position.avg_entry_price),
            'current_price': float(position.current_price),
            'market_value': float(position.market_value),
            'cost_basis': float(position.cost_basis),
            'unrealized_pl': float(position.unrealized_pl),
            'unrealized_plpc': float(position.unrealized_plpc) * 100
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """
    Obtiene todas las órdenes
    Ejemplo: GET /api/orders?status=open
    
    Parámetros:
    - status: open, closed, all (default: open)
    - limit: número máximo de órdenes (default: 50)
    """
    try:
        status = request.args.get('status', 'open')
        limit = min(int(request.args.get('limit', 50)), 500)
        
        orders = alpaca.list_orders(status=status, limit=limit)
        
        result = []
        for order in orders:
            result.append({
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty),
                'side': order.side,
                'type': order.type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
            })
        
        return jsonify({
            'count': len(result),
            'orders': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market/status', methods=['GET'])
def get_market_status():
    """
    Obtiene el estado del mercado
    Ejemplo: GET /api/market/status
    """
    try:
        clock = alpaca.get_clock()
        
        return jsonify({
            'is_open': clock.is_open,
            'timestamp': clock.timestamp.isoformat(),
            'next_open': clock.next_open.isoformat(),
            'next_close': clock.next_close.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/market/calendar', methods=['GET'])
def get_market_calendar():
    """
    Obtiene el calendario del mercado
    Ejemplo: GET /api/market/calendar?days=7
    
    Parámetros:
    - days: número de días a obtener (default: 7)
    """
    try:
        from datetime import timedelta
        
        days = min(int(request.args.get('days', 7)), 30)
        start = datetime.now()
        end = start + timedelta(days=days)
        
        calendar = alpaca.get_calendar(
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d')
        )
        
        result = []
        for day in calendar:
            result.append({
                'date': day.date.isoformat(),
                'open': day.open,
                'close': day.close
            })
        
        return jsonify({
            'count': len(result),
            'calendar': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexión con Alpaca
        account = alpaca.get_account()
        alpaca_status = 'connected'
    except:
        alpaca_status = 'disconnected'
    
    return jsonify({
        'status': 'healthy',
        'service': 'Trading API Server',
        'alpaca_connection': alpaca_status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Trading API Server")
    print("=" * 60)
    print(f"📊 Conectado a: {ALPACA_BASE_URL}")
    print(f"🌐 Servidor corriendo en: http://localhost:5000")
    print("\n📋 Endpoints disponibles:")
    print("  - GET  /                              (Info de la API)")
    print("  - GET  /health                        (Health check)")
    print("  - GET  /api/stock/price/<symbol>      (Precio actual)")
    print("  - GET  /api/stock/quote/<symbol>      (Cotización bid/ask)")
    print("  - GET  /api/stock/bars/<symbol>       (Datos históricos)")
    print("  - GET  /api/account                   (Info de cuenta)")
    print("  - GET  /api/positions                 (Posiciones abiertas)")
    print("  - GET  /api/positions/<symbol>        (Posición específica)")
    print("  - GET  /api/orders                    (Órdenes)")
    print("  - GET  /api/market/status             (Estado del mercado)")
    print("  - GET  /api/market/calendar           (Calendario)")
    print("=" * 60)
    print("\n⚠️  IMPORTANTE: Configura tus variables de entorno:")
    print("   export ALPACA_API_KEY='tu_key'")
    print("   export ALPACA_SECRET_KEY='tu_secret'")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

