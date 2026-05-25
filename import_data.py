import pandas as pd
from app import app, db
from models import Nasabah

# 1. Baca file dataset asli kamu
csv_file = "Loan Eligibility Prediction.csv"
try:
    df = pd.read_csv(csv_file)
    print(f"Berhasil membaca {len(df)} baris dari CSV.")
except FileNotFoundError:
    print(f"Error: File {csv_file} tidak ditemukan di folder ini!")
    exit()

# 2. Masukkan ke dalam database Flask
with app.app_context():
    # Opsional: Hapus semua data dummy yang dibikin Claude sebelumnya
    db.session.query(Nasabah).delete()
    db.session.commit()
    print("Data dummy berhasil dihapus dari database.")

    # Looping untuk memasukkan data CSV ke tabel Nasabah
    print("Mulai import data CSV ke database...")
    for index, row in df.iterrows():
        # Karena di datasetmu nggak ada nama, kita buat nama otomatis
        nama_otomatis = f"Nasabah {row['Customer_ID']}"
        
        nasabah_baru = Nasabah(
            customer_id=str(row['Customer_ID']),
            name=nama_otomatis,
            applicant_income=float(row['Applicant_Income']),
            coapplicant_income=float(row['Coapplicant_Income']),
            credit_history=int(row['Credit_History']),
            loan_amount=float(row['Loan_Amount']),
            dependents=int(row['Dependents'])
        )
        db.session.add(nasabah_baru)
    
    # Simpan perubahan ke database
    db.session.commit()
    print("Mantap! 614 Data Nasabah berhasil diimport ke Database SPK Kredit.")