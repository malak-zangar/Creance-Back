from collections import defaultdict
from datetime import datetime
from email.utils import parsedate
from flask_jwt_extended import jwt_required
from flask import Blueprint, jsonify
import os
from contrat.model import Contrats
from contrat.view import get_contrat_by_id
from dashboard.utils import formater_montant_euro, get_param_entreprise_by_id
from facture.model import Factures

dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard.route('/factureStats', methods=['GET'])
@jwt_required()
def facture_stats():
      
    factures = Factures.query.all()
    serialized_factures = [facture.serialize() for facture in factures]

    stats = {
        "Payée": {"count": 0, "total_montant": 0.0},
        "Échue": {"count": 0, "total_montant": 0.0},
        "Non échue": {"count": 0, "total_montant": 0.0}
    }

    for facture in serialized_factures:
        statut = facture['statut'] 
        base_currency = facture['devise']
        amount = float(facture['montant'])
        
        contrat = get_contrat_by_id(facture['contrat_id'])[0].json['contrat']
        param_entreprise = get_param_entreprise_by_id(contrat['paramentrep_id'])['param_entreprise']

        if base_currency == 'TND':
            conversion_rate=param_entreprise['tauxTndEur']
        elif base_currency == 'USD':
            conversion_rate=param_entreprise['tauxUsdEur']
        else:
            conversion_rate = 1 

        amount *= conversion_rate

        stats[statut]["count"] += 1
        stats[statut]["total_montant"] += float(formater_montant_euro(amount))

    print(jsonify(stats))
    return jsonify(stats)

@dashboard.route('/getTauxRecouvrement', methods=['GET'])
@jwt_required()
def get_taux_recouvrement():
    factures = Factures.query.all()
    serialized_factures = [facture.serialize() for facture in factures]

    total_ca = 0.0
    total_paye = 0.0

    total_factures = len(factures)


    for facture in serialized_factures:
        statut = facture['statut']
        base_currency = facture['devise']  
        amount = facture['montant']
 
        contrat = get_contrat_by_id(facture['contrat_id'])[0].json['contrat']
        param_entreprise = get_param_entreprise_by_id(contrat['paramentrep_id'])['param_entreprise']

        if base_currency == 'TND':
            conversion_rate=param_entreprise['tauxTndEur']
        elif base_currency == 'USD':
            conversion_rate=param_entreprise['tauxUsdEur']
        else:
            conversion_rate = 1 

        amount *= conversion_rate

        total_ca += amount

        if statut == "Payée":
            total_paye += amount

    if total_ca == 0:
        taux_recouvrement = 0.0
    else:
        taux_recouvrement = (total_paye / total_ca) * 100

    return jsonify({
        "total_factures" : total_factures,
        "total_ca":  float(formater_montant_euro(total_ca)),
        "total_paye": float(formater_montant_euro(total_paye)),
        "taux_recouvrement": float(formater_montant_euro(taux_recouvrement))
    })

@dashboard.route('/getPourcentageFactures', methods=['GET'])
@jwt_required()
def get_pourcentage_factures():
    factures = Factures.query.filter(Factures.statut != "Payée").all()
    
    total_factures = len(factures)
    echues = 0
    non_echues = 0

    for facture in factures:
        statut = facture.statut
        
        if statut == "Échue":
            echues += 1
        elif statut == "Non échue":
            non_echues += 1

    pourcentage_echues = (echues / total_factures) * 100 if total_factures else 0
    pourcentage_non_echues = (non_echues / total_factures) * 100 if total_factures else 0

    return jsonify({
        "total_factures": total_factures,
        "echues": echues,
        "non_echues" : non_echues,
        "pourcentage_echues": pourcentage_echues,
        "pourcentage_non_echues": pourcentage_non_echues
    })

@dashboard.route('/getOldestFactures', methods=['GET'])
@jwt_required()
def get_oldest_factures():

    factures = (Factures.query
            .filter(Factures.statut == 'Échue')
            .order_by(Factures.echeance.asc())
            .limit(5)
            .all()
        )
    serialized_factures = [facture.serialize() for facture in factures]
    data = []
    for facture in serialized_factures:

        base_currency = facture['devise']  
        amount = facture['montant']
 
        contrat = get_contrat_by_id(facture['contrat_id'])[0].json['contrat']
        param_entreprise = get_param_entreprise_by_id(contrat['paramentrep_id'])['param_entreprise']

        if base_currency == 'TND':
            conversion_rate=param_entreprise['tauxTndEur']
        elif base_currency == 'USD':
            conversion_rate=param_entreprise['tauxUsdEur']
        else:
            conversion_rate = 1 

        amount *= conversion_rate

        data.append({
        'numero': facture['numero'],
        'client': facture['client'],
        'retard': facture['retard'], 
        'montant': formater_montant_euro(amount)  
    })

    return jsonify(data)

#GetUnpaidClientfactures
@dashboard.route('/TopUnpaidClients', methods=['GET'])
@jwt_required()
def get_unpaid_clients_factures():

    unpaid_factures = Factures.query.filter(Factures.statut != 'Payée').all()
    serialized_factures = [facture.serialize() for facture in unpaid_factures]

    factures_by_client = defaultdict(lambda: {'factures': [], 'client_name': None})

    for facture in serialized_factures:
        client_id = facture['client_id']
        client_name = facture['client']  

        if isinstance(client_name, dict):
            client_name = client_name.get('name', 'Unknown') 

        factures_by_client[client_id]['factures'].append(facture)
        
        if factures_by_client[client_id]['client_name'] is None:
            factures_by_client[client_id]['client_name'] = client_name
        
        base_currency = facture['devise']
        amount = facture['montant']
        contrat = get_contrat_by_id(facture['contrat_id'])[0].json['contrat']
        param_entreprise = get_param_entreprise_by_id(contrat['paramentrep_id'])['param_entreprise']
        

        if base_currency == 'TND':
            conversion_rate = param_entreprise.get('tauxTndEur', 1)
        elif base_currency == 'USD':
            conversion_rate = param_entreprise.get('tauxUsdEur', 1)
        else:
            conversion_rate = 1 

        amount_in_eur = amount * conversion_rate
        facture['montant'] = amount_in_eur


    result = []
    for client_id, data in factures_by_client.items():
        factures = data['factures']

        total = sum(facture['montant'] for facture in factures)
        result.append({
            'client_id': client_id,
            'client': data['client_name'],
            'factures': factures,
            'total': total
        })

    top_clients = sorted(result, key=lambda x: x['total'], reverse=True)[:5]

    return jsonify(top_clients)


#GetCAevolution
@dashboard.route('/CAevolution', methods=['GET'])
@jwt_required()
def get_ca_evolution():

    factures = Factures.query.all()
    serialized_factures = [facture.serialize() for facture in factures]

    factures_by_mois = defaultdict(lambda: {'factures': []})

    for facture in serialized_factures:
     
        date_obj = facture['date']
        mois = date_obj.strftime('%m')  
        factures_by_mois[mois]['factures'].append(facture)
        
        base_currency = facture['devise']
        amount = facture['montant']
        contrat = get_contrat_by_id(facture['contrat_id'])[0].json['contrat']
        param_entreprise = get_param_entreprise_by_id(contrat['paramentrep_id'])['param_entreprise']
        

        if base_currency == 'TND':
            conversion_rate = param_entreprise.get('tauxTndEur', 1)
        elif base_currency == 'USD':
            conversion_rate = param_entreprise.get('tauxUsdEur', 1)
        else:
            conversion_rate = 1 

        amount_in_eur = amount * conversion_rate
        facture['montant'] = amount_in_eur


    result = []
    for mois, data in factures_by_mois.items():
        factures = data['factures']

        total = sum(facture['montant'] for facture in factures)
        result.append({
            'mois': mois,
            'factures': factures,
            'total': total
        })
   
    sortedRes = sorted(result, key=lambda x: x['mois'], reverse=False)

    return jsonify(sortedRes)

#GetCreanceEvolution
@dashboard.route('/CreanceEvolution', methods=['GET'])
@jwt_required()
def get_creance_evolution():
    factures = Factures.query.all()
    serialized_factures = [facture.serialize() for facture in factures]

    factures_by_mois = defaultdict(lambda: {'factures': [], 'count': 0})

    for facture in serialized_factures:
        date_obj = facture['date']
        mois = date_obj.strftime('%m') 
        factures_by_mois[mois]['factures'].append(facture)
        factures_by_mois[mois]['count'] += 1  

    result = []
    for mois, data in factures_by_mois.items():
        factures = data['factures']
        result.append({
            'mois': mois,
            'factures': factures,
            'count': data['count']  
        })

    sortedRes = sorted(result, key=lambda x: x['mois'], reverse=False)  

    return jsonify(sortedRes)

#GetTotalContratActifs
@dashboard.route('/totalContratActifs', methods=['GET'])
@jwt_required()
def contrat_stats():
    current_date = datetime.now().date()
    actif_contrats = Contrats.query.filter(Contrats.dateFin >= current_date).all()
    actif = len(actif_contrats)
    total = len(Contrats.query.all())
    pourcentage_actif = (actif / total) * 100 if total else 0

    return jsonify({'totalContratActif': actif,
                    "pourcentageActif" :pourcentage_actif })
