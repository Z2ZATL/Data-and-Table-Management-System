from app import db
from datetime import datetime

class FormSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=True)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FormSubmission {self.id}: {self.full_name}>"
