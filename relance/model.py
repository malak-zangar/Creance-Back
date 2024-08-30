from db import db

class EmailCascade(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    objet = db.Column(db.String(255), nullable=False)
    corps = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    dateInsertion = db.Column(db.DateTime, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'objet': self.objet,
            'corps': self.corps,
            'type': self.type,
            'dateInsertion': self.dateInsertion,
        }
