from flask import Blueprint, request, jsonify
import requests

paramentreprise = Blueprint('paramentreprise', __name__, url_prefix='/paramentreprise')

@paramentreprise.route('/convert', methods=['GET'])
def convert_currency():
    api_key = "8e2c386920da3958a8b3336a"
    base_currency = request.args.get('base')
    target_currency = request.args.get('target')
    amount = float(request.args.get('amount', 1.0))  # Montant à convertir
    print(api_key,base_currency,target_currency,amount,'hhhhh')
    if not base_currency or not target_currency:
        return jsonify({'error': 'Base currency and target currency are required'})

    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
    print(url,'hhhhh')

    response = requests.get(url)
    print(response)
    data = response.json()

    if data.get('result') != 'success':
        return jsonify({'error': 'Unable to fetch data from the API'})

    exchange_rate = data['conversion_rates'].get(target_currency)
    if not exchange_rate:
        return jsonify({'error': f'Conversion rate for {target_currency} not available'})

    converted_amount = amount * exchange_rate

    return jsonify({
        'base_currency': base_currency,
        'target_currency': target_currency,
        'amount': amount,
        'converted_amount': converted_amount
    })