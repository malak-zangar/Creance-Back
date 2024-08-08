import requests
from flask import jsonify, request
from flask_jwt_extended import jwt_required

from contrat.model import Contrats
from paramEntreprise.model import ParamEntreprise

def get_param_entreprise_by_id(param_entreprise_id):
    param_entreprise = ParamEntreprise.query.get(param_entreprise_id)
    return {'param_entreprise': param_entreprise.serialize()}


def get_contrat_by_id(contrat_id):
    contrat = Contrats.query.get(contrat_id)
    return jsonify({ 'contrat': contrat.serialize() })

def formater_montant_euro(montant):
    return "{:.2f}".format(montant)