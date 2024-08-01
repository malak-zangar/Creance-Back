from operator import and_
from flask import Blueprint, current_app, render_template, request, jsonify, make_response
from datetime import date, datetime, timedelta
from flask_mail import Mail, Message
import weasyprint
from contrat.model import Contrats
from contrat.view import get_contrat_by_id
from facture.model import Factures
from db import db
from facture.utils import send_reminder_email, send_validation_email
from user.view import *
from sqlalchemy import cast, Integer
from flask_jwt_extended import jwt_required, get_jwt_identity


facture = Blueprint('facture', __name__, url_prefix='/facture')


#Add new facture
@facture.route('/create', methods=['POST'])
@jwt_required()
def create_facture():
    data = request.get_json()
    numero = data.get("numero")
    date = data.get("date")
    delai = int(data.get("delai"))
    montant = float(data.get("montant"))
    montantEncaisse = float(data.get("montantEncaisse"))
    actionRecouvrement = data.get("actionRecouvrement")
    contrat_id = int(data.get("contrat_id"))
    actif = False


    if delai < 1 :
        return jsonify({
            "erreur": "le délai doit etre au moins égal à 1 jour"
        }), 400


    if not (numero and date and delai and montant and montantEncaisse is not None and actionRecouvrement and contrat_id ):
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
    


    new_facture = Factures(numero=numero, date=date,echeance=echeance,statut=statut,delai=delai,montant=montant,
                montantEncaisse=montantEncaisse, solde=solde, retard=retard, 
                 actionRecouvrement=actionRecouvrement, actif=actif ,contrat_id=contrat_id,dateFinalisation=dateFinalisation )
    db.session.add(new_facture)
    db.session.commit()
    send_validation_email(new_facture)

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
        return jsonify({"message": "Aucun contrat trouvé pour ce client"}), 404
    
    factures = Factures.query.filter(Factures.contrat_id.in_([contrat.id for contrat in contrats])).order_by(Factures.date.desc()).all()
    
    if not factures:
        return jsonify({"message": "Aucune facture trouvée pour ce client"}), 404
    
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
    

@facture.route('/report/<int:facture_id>',methods=['GET'])
@jwt_required()
def report(facture_id):
    facture = Factures.query.get_or_404(facture_id)
    facture_data = facture.serialize()

    html = render_template('facture_report.html', facture=facture_data)
    
    pdf = weasyprint.HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=report_facture_{facture_id}.pdf'

    return response


@facture.route('/send-reminder')
def schedule_reminders():
    
    factures = Factures.query.filter(Factures.statut !='Payée').all()
    now = datetime.now()
    for facture in factures:
        if facture.echeance - now <= timedelta(days=7):
            send_reminder_email(facture)
    return 'Reminders scheduled!'

#GetPaidfactures
@facture.route('/getAllPaid', methods=['GET'])
@jwt_required()
def get_all_paid_factures():
    paid_factures = Factures.query.filter(Factures.statut =='Payée').order_by(Factures.dateFinalisation.desc()).all()
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
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500