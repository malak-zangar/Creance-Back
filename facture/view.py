import sys
from flask import Blueprint, current_app, render_template, request, jsonify, make_response, send_file
from datetime import  datetime, timedelta
from flask_mail import  Message
import weasyprint
from contrat.model import Contrats
from contrat.view import get_contrat_by_id
from facture.model import Factures
from db import db
from facture.utils import parse_date, send_newfacture_email
from client.view import *
from flask_jwt_extended import jwt_required

from relance.model import EmailCascade

facture = Blueprint('facture', __name__, url_prefix='/facture')


#Add new facture
@facture.route('/create', methods=['POST'])
@jwt_required()
def create_facture():
    data = request.get_json()
    numero = data.get("numero")
    date = data.get("date")
    delai = get_contrat_by_id(int(data.get("contrat_id")))[0].json['contrat']['delai']
    montant = float(data.get("montant"))
    montantEncaisse = float(data.get("montantEncaisse"))
    contrat_id = int(data.get("contrat_id"))
    actif = False
    actifRelance = True
    nbrRelance = 0


    if delai < 1 :
        return jsonify({
            "erreur": "le délai doit etre au moins égal à 1 jour"
        }), 400


    if not (numero and date and delai and montant and montantEncaisse is not None and contrat_id ):
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

    dateFinalisation = None

    if solde == 0:
        statut = "Payée"
        dateFinalisation = today.strftime('%Y-%m-%d')
    elif retard != 0 :
        statut = "Échue"
    else:
        statut = "Non échue"
        dateFinalisation = None    
    
    if Factures.query.filter_by(numero=numero).first() is not None:
        return jsonify({'erreur': "Numéro de facture existe déja"}), 409
    

    new_facture = Factures(numero=numero, date=date,echeance=echeance,statut=statut,montant=montant,
                montantEncaisse=montantEncaisse, solde=solde, retard=retard, nbrRelance=nbrRelance, 
                 actif=actif ,contrat_id=contrat_id,dateFinalisation=dateFinalisation,actifRelance=actifRelance )
    db.session.add(new_facture)
    db.session.commit()
    send_newfacture_email(new_facture.serializeForEmail(),new_facture)

    return make_response(jsonify({"message": "facture crée avec succes", "facture": new_facture.serialize()}), 201)


#GetfactureByID
@facture.route('/getByID/<int:id>',methods=['GET'])
@jwt_required()
def get_facture_by_id(id):
    facture = Factures.query.get(id)

    if not facture:
        
        return jsonify({"message": "facture n'existe pas"}), 404

    
    return jsonify({
        'message': "facture existe :",
        'facture': facture.serialize()
    }), 200

#GetfactureByIDSerializedForEmail
@facture.route('/getByIDSerializedForEmail/<int:id>',methods=['GET'])
@jwt_required()
def get_facture_by_id_SerializedForEmail(id):
    facture = Factures.query.get(id)

    if not facture:
        
        return jsonify({"message": "facture n'existe pas"}), 404

    
    return jsonify({
        'message': "facture existe :",
        'facture': facture.serializeForEmail()
    }), 200



# Get clients with active unpaid invoices
@facture.route('/getClientsWithUnpaidInvoices', methods=['GET'])
def get_clients_with_active_unpaid_invoices():
    clients = Users.query.filter_by(actif=True).all()
    result = []

    for client in clients:
        contrats = Contrats.query.filter_by(client_id=client.id).all()
        contrat_ids = [contrat.id for contrat in contrats]

        if contrat_ids:
            unpaid_invoices = Factures.query.filter(
                Factures.contrat_id.in_(contrat_ids),
                Factures.statut != 'Payée'
            ).order_by(Factures.date.desc()).all()

            if unpaid_invoices:
                result.append(client.serialize())

    return jsonify(result), 200


#GetFacturesByClient
@facture.route('/getByClient/<int:client_id>', methods=['GET'])
@jwt_required()
def get_factures_by_client(client_id):
    contrats = Contrats.query.filter_by(client_id=client_id).all()
    
    if not contrats:
        return make_response(jsonify({"message": "Aucun contrat trouvé pour ce client"}), 404)
    
    factures = Factures.query.filter(Factures.contrat_id.in_([contrat.id for contrat in contrats])).order_by(Factures.date.desc()).all()
    
    if not factures:
        return make_response(jsonify({"message": "Aucune facture trouvée pour ce client"}), 404)
    
    serialized_factures = [facture.serialize() for facture in factures]
    return make_response(jsonify(serialized_factures), 200)


#GetFacturesByClient
@facture.route('getByClient/actif/<int:client_id>', methods=['GET'])
@jwt_required()
def get_actif_factures_by_client(client_id):

    contrats = Contrats.query.filter_by(client_id=client_id).all()
    
    if not contrats:
        return jsonify({"message": "Aucun contrat trouvé pour ce client"}), 404
    
    factures = Factures.query.filter(
            Factures.contrat_id.in_([contrat.id for contrat in contrats]),
          #  Factures.actif == True,
              Factures.solde != 0,
    ).order_by(Factures.date.desc()).all()

    if not factures:
        return jsonify({"message": "Aucune facture active trouvée pour ce client"}), 404
    
    serialized_factures = [facture.serialize() for facture in factures]
    return make_response(jsonify(serialized_factures), 200)

   
#activerfacture
@facture.route('/restaureFacture/<int:id>',methods=['PUT'])
@jwt_required()
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
@jwt_required()
def updateFacture(id):
    facture = Factures.query.get(id)

    if not facture:
        return jsonify({"message": "facture n'existe pas"}), 404

    data = request.get_json()
    facture.numero = data.get("numero",facture.numero)
    facture.date= parse_date(data.get("date",facture.date))
    facture.echeance = parse_date(data.get("echeance",facture.echeance))
    facture.statut = data.get("statut",facture.statut)
    facture.montant = float(data.get("montant",facture.montant))
    facture.montantEncaisse = float(data.get("montantEncaisse",facture.montantEncaisse))
    facture.solde = float(data.get("solde",facture.solde))
    facture.actif = data.get("actif",facture.actif)
    facture.nbrRelance = data.get("nbrRelance",facture.nbrRelance)
    facture.actifRelance = data.get("actifRelance",facture.actifRelance)


    if facture.montantEncaisse > facture.montant :
        return jsonify({
            "erreur": "Le montant encaissé ne peut pas être supérieur au montant total"
        }), 400
    
    if facture.solde > facture.montant:
        return jsonify({
            "erreur": "Le solde ne peut pas être supérieur au montant total"
        }), 400
    
    today = datetime.today().date()

    print (f" {type(facture.echeance)}")

    facture.retard = (today - facture.echeance).days if (today > facture.echeance and facture.solde != 0) else 0

    facture.solde= facture.montant - facture.montantEncaisse


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
        return jsonify({"message": "facture modifiée avec succés"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Echec de la modification de la facture"}), 500
    

@facture.route('/auto/<int:facture_id>',methods=['GET'])
def factAuto(facture_id):
    facture = Factures.query.get_or_404(facture_id)
    facture_data = facture.serialize_for_bill()
    html = render_template('invoice.html', facture=facture_data)
    pdf = weasyprint.HTML(string=html).write_pdf('./static/invoice.pdf')

    return send_file('./static/invoice.pdf')

@facture.route('/send-reminder')
def schedule_reminders():
    from app import mail,app

    with app.app_context():
        current_date = datetime.now().date()  

        overdue_invoices = Factures.query.filter(Factures.echeance < datetime.now(),Factures.statut == 'Échue',Factures.actifRelance == True).all()
        for invoice in overdue_invoices:
        
            serialized_invoice = invoice.serializeForEmail()
            next_reminder_date = serialized_invoice['echeance'] + timedelta(days=(serialized_invoice['nbrRelance'] + 1) * serialized_invoice['delaiRelance'])
            next_reminder_date = next_reminder_date.date()  
            if current_date == next_reminder_date and serialized_invoice['nbrRelance'] < serialized_invoice['maxRelance']:
                email_param = EmailCascade.query.filter_by(type='Relance').first()
    
                subject = email_param.objet.replace("[Numéro de facture]", serialized_invoice['numero']).replace("[Nom de l'entreprise]", serialized_invoice['nomEntrep'])

                body = email_param.corps.replace("[Nom du client]", serialized_invoice['client']) \
                                          .replace("[Numéro de facture]", serialized_invoice['numero']) \
                                          .replace("[Montant de la facture]", str(serialized_invoice['montant'])) \
                                        .replace("[Devise de la facture]", serialized_invoice['devise']) \
                                        .replace("[nombre de relance]", str(serialized_invoice['nbrRelance']+1)) \
                                          .replace("[Date d'échéance de paiement]", serialized_invoice['echeance'].strftime("%d/%m/%Y")) \
                                          .replace("[Nom de l'entreprise]", serialized_invoice['nomEntrep'])\
                                            .replace("[retard]", str(serialized_invoice['retard']))

                msg = Message(
                    subject,
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[serialized_invoice['email']]
                )
                msg.body = body    
                mail.send(msg)
                invoice.nbrRelance = serialized_invoice['nbrRelance'] + 1

                if serialized_invoice['nbrRelance'] >= serialized_invoice['maxRelance']:
                    last_reminder_date = serialized_invoice['echeance'] + timedelta(days=serialized_invoice['nbrRelance'] * serialized_invoice['delaiRelance'])
                    last_reminder_date=last_reminder_date.date()
                    if current_date >= last_reminder_date + timedelta(days=3):
                        invoice.statut = 'Fermée'

                db.session.commit()

        return "Reminders scheduled", 200

@facture.route('/retard-counter')
def retard_counter():
    
    factures = Factures.query.all()
    today = datetime.now().date()  
    for facture in factures:
        facture_echeance = facture.echeance
        if isinstance(facture_echeance, datetime):
            facture_echeance = facture_echeance.date()  # Convert echeance to date if it's datetime

        if today > facture_echeance and facture.solde != 0:
            facture.retard = (today - facture_echeance).days
            facture.statut="Échue"
        else:
            facture.retard = 0   
        
        db.session.commit()
    return 'Retard Counted!'


#GetPaidfactures
@facture.route('/getAllPaid', methods=['GET'])
@jwt_required()
def get_all_paid_factures():
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    
    if start_date and end_date:
        paid_factures = Factures.query.filter(Factures.statut =='Payée', Factures.dateFinalisation.between(start_date, end_date)).order_by(Factures.dateFinalisation.desc()).all()
    serialized_factures = [facture.serialize() for facture in paid_factures]
    return jsonify(serialized_factures)

#GetUnpaidfactures
@facture.route('/getAllUnpaid', methods=['GET'])
@jwt_required()
def get_all_unpaid_factures():
    unpaid_factures = Factures.query.filter(Factures.statut !='Payée').order_by(Factures.echeance.desc()).all()
    serialized_factures = [facture.serialize() for facture in unpaid_factures]
    return jsonify(serialized_factures)


    #export to csv

@facture.route('/export/csv',methods=['GET'])
@jwt_required()
def export_csv_factures():
    try :
        columns = request.args.get('columns')
        if columns:
            columns = columns.split(',')
        else:
            columns = ['numero','statut' ]  # Default columns

        factures = Factures.query.filter(Factures.statut!='Payée').all()
        factures_list = [facture.serialize_for_export() for facture in factures]
        for col in columns:
            if col not in factures_list[0]:
                return Response(
                    f"Column '{col}' does not exist in facture data",
                    status=400
                )

        filtered_factures_list = [{col: facture[col] for col in columns} for facture in factures_list]
        
        df = pd.DataFrame(filtered_factures_list)
        output = io.StringIO()
        df.to_csv(output, index=False,encoding='utf-8')
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv;charset=utf-8',
            headers={"Content-Disposition": "attachment;filename=facturesEncours.csv"}
              )
    except Exception as e:
        return jsonify({"error": str(e)}), 500