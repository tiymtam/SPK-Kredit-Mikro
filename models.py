"""
models.py
Database models for SPK Kredit Usaha Mikro using Flask-SQLAlchemy.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Nasabah(db.Model):
    """
    Model representing a loan applicant (nasabah).
    Stores all raw criteria data needed for AHP-SAW calculation.
    """
    __tablename__ = 'nasabah'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Criteria columns
    applicant_income = db.Column(db.Float, nullable=False, default=0.0)
    coapplicant_income = db.Column(db.Float, nullable=False, default=0.0)
    credit_history = db.Column(db.Integer, nullable=False, default=1)  # 0 or 1
    loan_amount = db.Column(db.Float, nullable=False, default=0.0)
    dependents = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Nasabah {self.customer_id} - {self.name}>'

    def to_dict(self):
        """Convert model instance to dictionary for easy template access."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'name': self.name,
            'applicant_income': self.applicant_income,
            'coapplicant_income': self.coapplicant_income,
            'credit_history': self.credit_history,
            'loan_amount': self.loan_amount,
            'dependents': self.dependents,
        }
