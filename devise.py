from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
BASE_URL = "https://v6.exchangeratesapi.io/latest"

@app.route('/convert', methods=['GET'])
def convert_currency():
    base_currency = request.args.get('base')
    target_currency = request.args.get('target')
    
    params = {
        'base': base_currency,
        'symbols': target_currency
    }
    
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    
    if 'error' in data:
        return jsonify({'error': 'Unable to fetch data'})
    
    exchange_rate = data['rates'].get(target_currency)
    if not exchange_rate:
        return jsonify({'error': 'Invalid currency'})
    
    amount = float(request.args.get('amount', 1.0))
    converted_amount = amount * exchange_rate
    
    return jsonify({
        'base_currency': base_currency,
        'target_currency': target_currency,
        'amount': amount,
        'converted_amount': converted_amount
    })

if __name__ == '__main__':
    app.run(debug=True)
