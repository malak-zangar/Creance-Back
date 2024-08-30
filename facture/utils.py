from datetime import date, datetime, timedelta
import sys
from flask import current_app, jsonify
from flask_mail import Message
from db import db
from facture.model import Factures
from relance.model import EmailCascade

def updateFactureAfterEncaissement(id, montant_encaisse):
    facture = Factures.query.get(id)

    if not facture:
        return (False, jsonify({"message": "facture n'existe pas"})), 404
    
    if montant_encaisse > facture.solde:
        return (False, jsonify({
            "erreur": "montant à encaisser supérieur au solde"
        })), 400

    facture.montantEncaisse += montant_encaisse
    facture.solde -= montant_encaisse

    today = datetime.today()

    if facture.solde == 0:
        facture.statut = "Payée"
        facture.dateFinalisation = today.strftime('%Y-%m-%d')

    try:
        db.session.commit()  # Commit the changes to the database
        return (True, "Facture mise à jour avec succès")  # Return success status and message
    except Exception as e:
        db.session.rollback()  # Rollback the changes if an error occurs
        return (False, jsonify({"erreur": "Erreur lors de la mise à jour de la facture"})), 500


def updateFactureAfterCancelEncaissement(id, montant_encaisse):
    facture = Factures.query.get(id)

    if not facture:
        return (False, jsonify({"message": "facture n'existe pas"})), 404

    facture.montantEncaisse -= montant_encaisse
    facture.solde += montant_encaisse
    today = datetime.today()
   # Mettre à jour le statut de la facture en fonction de la date d'échéance
    if facture.echeance < today:
        facture.statut = "Échue"
    
    else:
        facture.statut = "Non échue"
     
    facture.dateFinalisation = None


    try:
        db.session.commit()  
        return (True, "Facture mise à jour avec succès") 
    except Exception as e:
        db.session.rollback() 
        return (False, jsonify({"erreur": "Erreur lors de la mise à jour de la facture"})), 500


def send_reminder_email(facture):
    from app import mail
    from client.view import get_client_by_id

    from contrat.view import get_contrat_by_id

    client_email = get_client_by_id(get_contrat_by_id(facture.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['email']
    msg = Message(
        "Rappel de Facture",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[client_email]
    )
    msg.body = f"Bonjour, ceci est un rappel pour la facture {facture.numero} qui est due le {facture.echeance.strftime('%Y-%m-%d')}."
   # mail.send(msg)

def send_newfacture_email(facture,fact):
    from app import mail
    from contrat.view import get_contrat_by_id
    from client.view import get_client_by_id

    contrat = get_contrat_by_id(facture['contrat_id'])[0].json['contrat']
    client_id = contrat['client_id']
    client_email = get_client_by_id(client_id)[0].json['client']['email']
    today = datetime.today()
    
    email_param = EmailCascade.query.filter_by(type='Facture').first()
    subject = email_param.objet.replace("[Numéro de facture]", facture['numero']).replace("[Nom de l'entreprise]", facture['nomEntrep'])
    body = email_param.corps.replace("[Nom du client]", facture['client']) \
                                          .replace("[Numéro de facture]", facture['numero']) \
                                          .replace("[Montant de la facture]", str(facture['montant'])) \
                                        .replace("[Devise de la facture]", facture['devise']) \
                                        .replace("[Date de la facture]", facture['date'].strftime("%d/%m/%Y")) \
                                          .replace("[Date d'échéance de paiement]", facture['echeance'].strftime("%d/%m/%Y")) \
                                          .replace("[Nom de l'entreprise]", facture['nomEntrep'])

  
    msg = Message(
                    subject,
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[client_email]
                )
    msg.body=body
    mail.send(msg)

    if fact.solde == 0:
        fact.statut = "Payée"
        fact.dateFinalisation = today.strftime('%Y-%m-%d')
    elif fact.retard != 0 :
        fact.statut = "Échue"
    else:
        fact.statut = "Non échue"
        fact.dateFinalisation = None    
    try:
        db.session.commit()
        return True, None  
    except Exception as e:
        db.session.rollback()
        return False, jsonify({"message": "Erreur lors de la mise à jour de la facture"}), 500


def updateFactureAfterContractUpdate(facture, delay):
    today = datetime.today()
    facture.echeance = facture.date + timedelta(days=int(delay))
    facture.retard = (today - facture.echeance).days if (today > facture.echeance and facture.solde != 0) else 0

    if facture.solde == 0:
        facture.statut = "Payée"
    elif facture.retard != 0:
        facture.statut = "Échue"
    else:
        facture.statut = "Non échue"
        facture.dateFinalisation = None

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