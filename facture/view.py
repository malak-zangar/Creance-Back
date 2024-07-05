from flask import Blueprint, current_app, render_template, request, jsonify, make_response
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import weasyprint
from facture.model import Factures
from db import db
from user.view import get_client_by_id
from flask_login import login_required


facture = Blueprint('facture', __name__, url_prefix='/facture')


#Add new facture
@facture.route('/create', methods=['POST'])
#@login_required
def create_facture():
    data = request.get_json()
    numero = data.get("numero")
    date = data.get("date")
    delai = data.get("delai")
    montant = data.get("montant")
    montantEncaisse = data.get("montantEncaisse")
    actionRecouvrement = data.get("actionRecouvrement")
    client_id = data.get("client_id")
    actif = True


    if delai < 1 :
        return jsonify({
            "erreur": "le délai doit etre au moins égal à 1 jour"
        }), 400


    if not (numero and date and delai and montant and montantEncaisse is not None and actionRecouvrement and client_id ):
        return jsonify({
            "erreur": "svp entrer toutes les données"
        }), 400
    
    if montantEncaisse > montant:
        return jsonify({
            "erreur": "Le montant encaissé ne peut pas être supérieur au montant total"
        }), 400
    
    try:
        date = datetime.strptime(date, '%Y-%m-%d')
        echeance = date + timedelta(days=int(delai))

    except ValueError:
        return jsonify({
            "erreur": "Format de date ou délai invalide"
        }), 400
    
     # Calcul du solde
    solde = montant - montantEncaisse

    # Calcul du retard en jours
    today = datetime.today()
    retard = (today - echeance).days if (today > echeance and solde != 0) else 0



    # Détermination du statut en fonction du solde
    if solde == 0:
        statut = "payé"
        dateFinalisation = today.strftime('%Y-%m-%d')
    elif solde == montant:
        statut = "non payé"
        dateFinalisation = None
    else:
        statut = "en cours"
        dateFinalisation = None
    
    if Factures.query.filter_by(numero=numero).first() is not None:
        return jsonify({'erreur': "Numéro de facture existe déja"}), 409
    


    new_facture = Factures(numero=numero, date=date,echeance=echeance,statut=statut,delai=delai,montant=montant,
                montantEncaisse=montantEncaisse, solde=solde, retard=retard, dateFinalisation=dateFinalisation,
                   actionRecouvrement=actionRecouvrement, actif=actif ,client_id=client_id )
    db.session.add(new_facture)
    db.session.commit()
    return make_response(jsonify({"message": "facture crée avec succes", "facture": new_facture.serialize()}), 201)


#GetAll factures
@facture.route('/getAll', methods=['GET'])
#@login_required
def get_all_factures():
    factures = Factures.query.all()
    serialized_factures = [facture.serialize() for facture in factures]
    return make_response(jsonify(serialized_factures))

#GetActiffactures
@facture.route('/getAllActif', methods=['GET'])
#@login_required
def get_all_actif_factures():
    actif_factures = Factures.query.filter_by(actif=True).all()
    serialized_factures = [facture.serialize() for facture in actif_factures]
    return jsonify(serialized_factures)

#GetArchivedfactures
@facture.route('/getAllArchived', methods=['GET'])
#@login_required
def get_all_archived_factures():
    archived_factures = Factures.query.filter_by(actif=False).all()
    serialized_factures = [facture.serialize() for facture in archived_factures]
    return jsonify(serialized_factures)


#GetfactureByID
@facture.route('/getByID/<int:id>',methods=['GET'])
#@login_required
def get_facture_by_id(id):
    facture = Factures.query.get(id)

    if not facture:
        
        return jsonify({"message": "facture n'existe pas"}), 404

    
    return jsonify({
        'message': "facture existe :",
        'facture': facture.serialize()
    }), 200

#GetfactureBynumero
@facture.route('/getByNumero/<string:numero>',methods=['GET'])
#@login_required
def get_facture_by_numero(numero):
    facture = Factures.query.filter_by(numero=numero).first()

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404

    return jsonify({
        'message': "facture existe :",
        'facture': facture.serialize(),
    }), 200

#Archivefacture
@facture.route('/archiveFacture/<int:id>',methods=['PUT'])
#@login_required
def archiverFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404
    
    facture.actif=False

    try:
        db.session.commit()
        return jsonify({"message": "facture archivé avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans l'archivage du facture"}), 500
    

#Updatefacture
@facture.route('/updateFacture/<int:id>',methods=['PUT'])
#@login_required
def updateFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404

    data = request.get_json()
    facture.numero = data.get("numero",facture.numero)
    facture.date = data.get("date",facture.date)
    facture.echeance = data.get("echeance",facture.echeance)
    facture.statut = data.get("statut",facture.statut)
    facture.delai = data.get("delai",facture.delai)
    facture.montant = data.get("montant",facture.montant)
    facture.montantEncaisse = data.get("montantEncaisse",facture.montantEncaisse)
    facture.solde = data.get("solde",facture.solde)
    facture.actionRecouvrement = data.get("actionRecouvrement",facture.actionRecouvrement)
    facture.actif = data.get("actif",facture.actif)


    if facture.montantEncaisse > facture.montant:
        return jsonify({
            "erreur": "Le montant encaissé ne peut pas être supérieur au montant total"
        }), 400
    
    if facture.solde > facture.montant:
        return jsonify({
            "erreur": "Le solde ne peut pas être supérieur au montant total"
        }), 400
    
    try:
        #date = datetime.strptime(facture.date, '%Y-%m-%d')
        facture.echeance = facture.date + timedelta(days=int(facture.delai))

    except ValueError:
        return jsonify({
            "erreur": "Format de date ou délai invalide"
        }), 400

    # Calcul du retard en jours
    today = datetime.today()
    facture.retard = (today - facture.echeance).days if (today > facture.echeance and facture.solde != 0) else 0



    # Détermination du statut en fonction du solde
    if facture.solde == 0:
        facture.statut = "payé"
        facture.dateFinalisation = today.strftime('%Y-%m-%d')
    elif facture.solde == facture.montant:
        facture.statut = "non payé"
        facture.dateFinalisation = None
    else:
        facture.statut = "en cours"
        facture.dateFinalisation = None

    try:
        db.session.commit()
        return jsonify({"message": "facture modifiée avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification de la facture"}), 500
    


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



    # Détermination du statut en fonction du solde
    if facture.solde == 0:
        facture.statut = "payé"
        facture.dateFinalisation = today.strftime('%Y-%m-%d')
    elif facture.solde == facture.montant:
        facture.statut = "non payé"
        facture.dateFinalisation = None
    else:
        facture.statut = "en cours"
        facture.dateFinalisation = None

    try:
        db.session.commit()
        return True, None  
    except Exception as e:
        db.session.rollback()
        return False, jsonify({"message": "Erreur lors de la mise à jour de la facture"}), 500



#MarquerPayéfacture
@facture.route('/marquerpayeFacture/<int:id>',methods=['PUT'])
#@login_required
def marquerpayeFacture(id):
    

    facture = Factures.query.get(id)
    if not facture:
        return jsonify({"message": "Facture n'existe pas"}), 404
    
    facture.solde=0
    facture.montantEncaisse=facture.montant
    facture.statut = "payé"

    today = datetime.today()

    facture.dateFinalisation = today.strftime('%Y-%m-%d')

        # Calcul du retard en jours
    facture.retard = (today - facture.echeance).days if (today > facture.echeance and facture.solde != 0) else 0
    try:
        db.session.commit()
        return jsonify({"message": "facture marquée payée avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Echec du paiement de la facture: {str(e)}"}), 500    


@facture.route('/report/<int:facture_id>',methods=['GET'])
#@login_required
def report(facture_id):
    facture = Factures.query.get_or_404(facture_id)
    facture_data = facture.serialize()


    html = render_template('facture_report.html', facture=facture_data)
    
    pdf = weasyprint.HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=report_facture_{facture_id}.pdf'

    return response


def send_reminder_email(facture):
    from app import mail

    client_email = get_client_by_id(facture.client_id)[0].json['client']['email']
    msg = Message(
        "Rappel de Facture",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[client_email]
    )
    msg.body = f"Bonjour, ceci est un rappel pour la facture {facture.numero} qui est due le {facture.echeance.strftime('%Y-%m-%d')}."
    mail.send(msg)


@facture.route('/send-reminder')
def schedule_reminders():
    
    factures = Factures.query.filter(Factures.statut !='payé').all()
    now = datetime.now()
    for facture in factures:
        if facture.echeance - now <= timedelta(days=7):
            send_reminder_email(facture)
    return 'Reminders scheduled!'