"""
app.py
Main Flask application: configuration, routes, and CRUD logic
for SPK Kredit Usaha Mikro (AHP-SAW).
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Nasabah
from ahp_saw_engine import calculate_spk, get_criteria_meta

# ─────────────────────────────────────────────────────────────
#  App Configuration
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'spk-ahp-saw-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///spk_kredit.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ─────────────────────────────────────────────────────────────
#  Database initialization
# ─────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

    # Seed sample data if the table is empty
    if Nasabah.query.count() == 0:
        sample_data = [
            Nasabah(customer_id='LP001', name='Andi Pratama',       applicant_income=5000,  coapplicant_income=0,    credit_history=1, loan_amount=128,  dependents=0),
            Nasabah(customer_id='LP002', name='Budi Santoso',       applicant_income=4583,  coapplicant_income=1508, credit_history=1, loan_amount=128,  dependents=1),
            Nasabah(customer_id='LP003', name='Citra Dewi',         applicant_income=3000,  coapplicant_income=0,    credit_history=1, loan_amount=66,   dependents=0),
            Nasabah(customer_id='LP004', name='Dian Rahayu',        applicant_income=2583,  coapplicant_income=2358, credit_history=1, loan_amount=120,  dependents=0),
            Nasabah(customer_id='LP005', name='Eko Widodo',         applicant_income=6000,  coapplicant_income=0,    credit_history=1, loan_amount=141,  dependents=2),
            Nasabah(customer_id='LP006', name='Fitri Handayani',    applicant_income=2333,  coapplicant_income=1516, credit_history=1, loan_amount=95,   dependents=1),
            Nasabah(customer_id='LP007', name='Gilang Permana',     applicant_income=4583,  coapplicant_income=0,    credit_history=0, loan_amount=300,  dependents=2),
            Nasabah(customer_id='LP008', name='Hendra Kurniawan',   applicant_income=8167,  coapplicant_income=0,    credit_history=1, loan_amount=258,  dependents=0),
            Nasabah(customer_id='LP009', name='Indah Sari',         applicant_income=2333,  coapplicant_income=1516, credit_history=1, loan_amount=112,  dependents=3),
            Nasabah(customer_id='LP010', name='Joko Susilo',        applicant_income=3217,  coapplicant_income=0,    credit_history=1, loan_amount=56,   dependents=0),
            Nasabah(customer_id='LP011', name='Kartini Wulandari',  applicant_income=4500,  coapplicant_income=2000, credit_history=0, loan_amount=175,  dependents=2),
            Nasabah(customer_id='LP012', name='Lukman Hakim',       applicant_income=7000,  coapplicant_income=0,    credit_history=1, loan_amount=210,  dependents=1),
        ]
        db.session.bulk_save_objects(sample_data)
        db.session.commit()


# ─────────────────────────────────────────────────────────────
#  Helper: generate next customer ID
# ─────────────────────────────────────────────────────────────
def generate_customer_id():
    """Auto-generate a sequential customer ID like LP013, LP014, …"""
    last = Nasabah.query.order_by(Nasabah.id.desc()).first()
    if last and last.customer_id.startswith('LP'):
        try:
            num = int(last.customer_id[2:]) + 1
            return f'LP{num:03d}'
        except ValueError:
            pass
    count = Nasabah.query.count() + 1
    return f'LP{count:03d}'


# ─────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Landing / dashboard page."""
    total_nasabah = Nasabah.query.count()
    return render_template('dashboard.html', total_nasabah=total_nasabah)


@app.route('/nasabah')
def data_nasabah():
    """Display all nasabah records with CRUD controls."""
    nasabah_list = Nasabah.query.order_by(Nasabah.id).all()
    return render_template('data_nasabah.html', nasabah_list=nasabah_list)


@app.route('/nasabah/add', methods=['POST'])
def add_nasabah():
    """POST: Add a new Nasabah record."""
    try:
        credit_history = int(request.form.get('credit_history', 1))
        if credit_history not in (0, 1):
            flash('Credit History harus bernilai 0 atau 1.', 'danger')
            return redirect(url_for('data_nasabah'))

        new_nasabah = Nasabah(
            customer_id=generate_customer_id(),
            name=request.form.get('name', '').strip(),
            applicant_income=float(request.form.get('applicant_income', 0)),
            coapplicant_income=float(request.form.get('coapplicant_income', 0)),
            credit_history=credit_history,
            loan_amount=float(request.form.get('loan_amount', 0)),
            dependents=int(request.form.get('dependents', 0)),
        )

        if not new_nasabah.name:
            flash('Nama nasabah tidak boleh kosong.', 'danger')
            return redirect(url_for('data_nasabah'))

        db.session.add(new_nasabah)
        db.session.commit()
        flash(f'Nasabah "{new_nasabah.name}" berhasil ditambahkan.', 'success')

    except ValueError as e:
        flash(f'Input tidak valid: {e}', 'danger')

    return redirect(url_for('data_nasabah'))


@app.route('/nasabah/edit/<int:id>', methods=['POST'])
def edit_nasabah(id):
    """POST: Update an existing Nasabah record."""
    nasabah = Nasabah.query.get_or_404(id)
    try:
        credit_history = int(request.form.get('credit_history', 1))
        if credit_history not in (0, 1):
            flash('Credit History harus bernilai 0 atau 1.', 'danger')
            return redirect(url_for('data_nasabah'))

        nasabah.name = request.form.get('name', nasabah.name).strip()
        nasabah.applicant_income = float(request.form.get('applicant_income', nasabah.applicant_income))
        nasabah.coapplicant_income = float(request.form.get('coapplicant_income', nasabah.coapplicant_income))
        nasabah.credit_history = credit_history
        nasabah.loan_amount = float(request.form.get('loan_amount', nasabah.loan_amount))
        nasabah.dependents = int(request.form.get('dependents', nasabah.dependents))

        db.session.commit()
        flash(f'Data nasabah "{nasabah.name}" berhasil diperbarui.', 'success')

    except ValueError as e:
        flash(f'Input tidak valid: {e}', 'danger')

    return redirect(url_for('data_nasabah'))


@app.route('/nasabah/delete/<int:id>')
def delete_nasabah(id):
    """GET: Delete a Nasabah record by ID."""
    nasabah = Nasabah.query.get_or_404(id)
    name = nasabah.name
    db.session.delete(nasabah)
    db.session.commit()
    flash(f'Data nasabah "{name}" berhasil dihapus.', 'warning')
    return redirect(url_for('data_nasabah'))


@app.route('/hasil')
def hasil():
    """Run AHP-SAW calculation and display ranked results."""
    nasabah_list = Nasabah.query.all()
    ranked = calculate_spk(nasabah_list)
    criteria_meta = get_criteria_meta()
    top10 = ranked[:10]
    rest = ranked[10:]
    return render_template(
        'hasil.html',
        ranked=ranked,
        top10=top10,
        rest=rest,
        criteria_meta=criteria_meta,
        total=len(ranked),
    )


# ─────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
