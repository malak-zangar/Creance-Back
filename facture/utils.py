from datetime import date, datetime
from flask import current_app, jsonify
from flask_mail import Message
from contrat.view import get_contrat_by_id
from db import db
from facture.model import Factures
from user.view import get_client_by_id

#UpdatefactureAfterEncaissement
def updateFactureAfterEncaissement(id,montant_encaisse):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404
    if montant_encaisse>facture.solde :
        return jsonify({
            "erreur": "montant à encaisser supérieur au solde"
        }), 400

    
    facture.montantEncaisse += montant_encaisse

    facture.solde -= montant_encaisse

    today = datetime.today()



def send_reminder_email(facture):
    from app import mail

    client_email = get_client_by_id(get_contrat_by_id(facture.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['email']
    msg = Message(
        "Rappel de Facture",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[client_email]
    )
    msg.body = f"Bonjour, ceci est un rappel pour la facture {facture.numero} qui est due le {facture.echeance.strftime('%Y-%m-%d')}."
   # mail.send(msg)

def send_validation_email(facture):
    from app import mail

    contrat = get_contrat_by_id(facture.contrat_id)[0].json['contrat']
    client_id = contrat['client_id']
    client_email = get_client_by_id(client_id)[0].json['client']['email']
    today = datetime.today()

   # client_email = get_client_by_id(get_contrat_by_id(facture.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['email']
    msg = Message(
        "Validation de Facture",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[client_email]
    )
    msg.body = f"Bonjour, vous avez une nouvelle facture {facture.numero} à valider. Cliquez sur ce lien SVP : http://localhost:5173/factures/valider/{client_id}."    
    mail.send(msg)

    if facture.solde == 0:
        facture.statut = "Payée"
        facture.dateFinalisation = today.strftime('%Y-%m-%d')
    elif facture.retard != 0 :
        facture.statut = "Échue"
    else:
        facture.statut = "Non échue"
        facture.dateFinalisation = None    
    try:
        db.session.commit()
        return True, None  
    except Exception as e:
        db.session.rollback()
        return False, jsonify({"message": "Erreur lors de la mise à jour de la facture"}), 500


def parse_date(date_input):
        if isinstance(date_input, str):
            try:
                return datetime.strptime(date_input, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Invalid date format")
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, date):
            return date_input
        else:
            raise ValueError("Invalid date format")