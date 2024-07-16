from operator import and_
from flask import Blueprint, current_app, render_template, request, jsonify, make_response
from datetime import date, datetime, timedelta
from flask_mail import Mail, Message
import weasyprint
from contrat.model import Contrats
from contrat.view import get_contrat_by_id
from facture.model import Factures
from db import db
from user.view import *
from flask_login import login_required
from sqlalchemy import cast, Integer


facture = Blueprint('facture', __name__, url_prefix='/facture')


#Add new facture
@facture.route('/create', methods=['POST'])
#@login_required
def create_facture():
    data = request.get_json()
    numero = data.get("numero")
    date = data.get("date")
    delai = int(data.get("delai"))
    montant = float(data.get("montant"))
    montantEncaisse = float(data.get("montantEncaisse"))
    actionRecouvrement = data.get("actionRecouvrement")
    devise = data.get("devise")
    #client_id = int(data.get("client_id"))
    contrat_id = int(data.get("contrat_id"))
    actif = False


    if delai < 1 :
        return jsonify({
            "erreur": "le délai doit etre au moins égal à 1 jour"
        }), 400


    if not (numero and devise and date and delai and montant and montantEncaisse is not None and actionRecouvrement and contrat_id ):
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


    if retard != 0 :
        statut = "Échue"
    elif solde == 0:
        statut = "Payée"
        dateFinalisation = today.strftime('%Y-%m-%d')
    elif solde == montant:
        statut = "Non payée"
        dateFinalisation = None
    else:
        statut = "En cours"
        dateFinalisation = None
    
    if Factures.query.filter_by(numero=numero).first() is not None:
        return jsonify({'erreur': "Numéro de facture existe déja"}), 409
    


    new_facture = Factures(numero=numero, date=date,echeance=echeance,statut=statut,delai=delai,montant=montant,
                montantEncaisse=montantEncaisse, solde=solde, retard=retard, dateFinalisation=dateFinalisation,
                devise=devise, actionRecouvrement=actionRecouvrement, actif=actif ,contrat_id=contrat_id )
    db.session.add(new_facture)
    db.session.commit()
    send_validation_email(new_facture)

    return make_response(jsonify({"message": "facture crée avec succes", "facture": new_facture.serialize()}), 201)


#GetAll factures
@facture.route('/getAll', methods=['GET'])
#@login_required
def get_all_factures():
    factures = Factures.query.order_by(Factures.date.desc()).all()
    serialized_factures = [facture.serialize() for facture in factures]
    return make_response(jsonify(serialized_factures))

#GetActiffactures
@facture.route('/getAllActif', methods=['GET'])
#@login_required
def get_all_actif_factures():
    actif_factures = Factures.query.filter_by(actif=True).order_by(Factures.date.desc()).all()
    serialized_factures = [facture.serialize() for facture in actif_factures]
    return make_response(jsonify(serialized_factures))

#GetArchivedfactures
@facture.route('/getAllArchived', methods=['GET'])
#@login_required
def get_all_archived_factures():
    archived_factures = Factures.query.filter_by(actif=False).order_by(Factures.date.desc()).all()
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


# Get clients with active unpaid invoices
@facture.route('/getClientsWithActiveUnpaidInvoices', methods=['GET'])
def get_clients_with_active_unpaid_invoices():
    clients = Users.query.filter_by(actif=True).all()
    result = []

    for client in clients:
        contrats = Contrats.query.filter_by(client_id=client.id).all()
        contrat_ids = [contrat.id for contrat in contrats]

        if contrat_ids:
            unpaid_invoices = Factures.query.filter(
                Factures.contrat_id.in_(contrat_ids),
                Factures.actif == True,
                Factures.statut != 'Payée'
            ).order_by(Factures.date.desc()).all()

            if unpaid_invoices:
                result.append(client.serialize())

    return jsonify(result), 200


#GetFacturesByClient
@facture.route('/getByClient/<int:client_id>', methods=['GET'])
#@login_required
def get_factures_by_client(client_id):
    contrats = Contrats.query.filter_by(client_id=client_id).all()
    
    if not contrats:
        return jsonify({"message": "Aucun contrat trouvé pour ce client"}), 404
    
    factures = Factures.query.filter(Factures.contrat_id.in_([contrat.id for contrat in contrats])).order_by(Factures.date.desc()).all()
    
    if not factures:
        return jsonify({"message": "Aucune facture trouvée pour ce client"}), 404
    
    serialized_factures = [facture.serialize() for facture in factures]
    return make_response(jsonify(serialized_factures), 200)


#GetFacturesByClient
@facture.route('getByClient/actif/<int:client_id>', methods=['GET'])
#@login_required
def get_actif_factures_by_client(client_id):

    contrats = Contrats.query.filter_by(client_id=client_id).all()
    
    if not contrats:
        return jsonify({"message": "Aucun contrat trouvé pour ce client"}), 404
    
    factures = Factures.query.filter(
            Factures.contrat_id.in_([contrat.id for contrat in contrats]),
            Factures.actif == True,
    ).order_by(Factures.date.desc()).all()

    if not factures:
        return jsonify({"message": "Aucune facture active trouvée pour ce client"}), 404
    
    serialized_factures = [facture.serialize() for facture in factures]
    return make_response(jsonify(serialized_factures), 200)



#GetfactureBynumero
@facture.route('/getByNumero/<string:numero>',methods=['GET'])
#@login_required
def get_facture_by_numero(numero):
    facture = Factures.query.filter(cast(numero, Integer) == numero).first()

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
    
#activerfacture
@facture.route('/restaureFacture/<int:id>',methods=['PUT'])
#@login_required
def activerFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404
    
    facture.actif=True

    try:
        db.session.commit()
        return jsonify({"message": "facture restaurée avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec dans la restauration du facture"}), 500
    


#Updatefacture
@facture.route('/updateFacture/<int:id>',methods=['PUT'])
#@login_required
def updateFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404
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

    data = request.get_json()
    facture.numero = data.get("numero",facture.numero)
    #facture.date = date(data.get("date",facture.date))
    facture.date= parse_date(data.get("date",facture.date))
    #facture.echeance = date(data.get("echeance",facture.echeance))
    facture.echeance = parse_date(data.get("echeance",facture.echeance))
    facture.statut = data.get("statut",facture.statut)
    facture.delai = data.get("delai",facture.delai)
    facture.montant = float(data.get("montant",facture.montant))
    facture.montantEncaisse = float(data.get("montantEncaisse",facture.montantEncaisse))
    facture.solde = float(data.get("solde",facture.solde))
    facture.actionRecouvrement = data.get("actionRecouvrement",facture.actionRecouvrement)
    facture.actif = data.get("actif",facture.actif)
    facture.devise = data.get("devise",facture.devise)


    if facture.montantEncaisse > facture.montant :
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
    #today = parse_date(datetime.today())
    today = datetime.today().date()

    print (f" {type(facture.echeance)}")

    facture.retard = (today - facture.echeance).days if (today > facture.echeance and facture.solde != 0) else 0

    facture.solde= facture.montant - facture.montantEncaisse

    if facture.retard != 0 :
        facture.statut = "Échue"
    elif facture.solde == 0:
        facture.statut = "Payée"
        facture.dateFinalisation = today.strftime('%Y-%m-%d')
    elif facture.solde == facture.montant:
        facture.statut = "Non payée"
        facture.dateFinalisation = None
    else:
        facture.statut = "En cours"
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



    if facture.retard != 0 :
        facture.statut = "Échue"
    elif facture.solde == 0:
        facture.statut = "Payée"
        facture.dateFinalisation = today.strftime('%Y-%m-%d')
    elif facture.solde == facture.montant:
        facture.statut = "Non payée"
        facture.dateFinalisation = None
    else:
        facture.statut = "En cours"
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
    facture.statut = "Payée"

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

   # client_email = get_client_by_id(get_contrat_by_id(facture.contrat_id)[0].json['contrat']['client_id'])[0].json['client']['email']
    msg = Message(
        "Validation de Facture",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[client_email]
    )
    msg.body = f"Bonjour, vous avez une nouvelle facture {facture.numero} à valider. Cliquez sur ce lien SVP : http://localhost:5173/factures/valider/{client_id}."    
    mail.send(msg)


@facture.route('/send-reminder')
def schedule_reminders():
    
    factures = Factures.query.filter(Factures.statut !='Payée').all()
    now = datetime.now()
    for facture in factures:
        if facture.echeance - now <= timedelta(days=7):
            send_reminder_email(facture)
    return 'Reminders scheduled!'