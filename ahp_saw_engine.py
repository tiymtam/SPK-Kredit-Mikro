"""
ahp_saw_engine.py
Core SPK calculation logic using AHP weights and SAW normalization/scoring.
"""


# ─────────────────────────────────────────────────────────────
#  Fixed AHP Weights (pre-computed from pairwise comparison matrix)
#  K1 Income (Benefit):          0.2177
#  K2 Credit History (Benefit):  0.5308
#  K3 Loan Amount (Cost):        0.1035
#  K4 Dependents (Cost):         0.1480
# ─────────────────────────────────────────────────────────────
AHP_WEIGHTS = {
    'K1': 0.2177,
    'K2': 0.5308,
    'K3': 0.1035,
    'K4': 0.1480,
}

CRITERIA_META = [
    {'key': 'K1', 'label': 'Total Income',      'type': 'benefit', 'weight': AHP_WEIGHTS['K1']},
    {'key': 'K2', 'label': 'Credit History',    'type': 'benefit', 'weight': AHP_WEIGHTS['K2']},
    {'key': 'K3', 'label': 'Loan Amount',       'type': 'cost',    'weight': AHP_WEIGHTS['K3']},
    {'key': 'K4', 'label': 'Dependents (+1)',   'type': 'cost',    'weight': AHP_WEIGHTS['K4']},
]


def calculate_spk(nasabah_list):
    """
    Run the AHP-SAW Decision Support calculation on a list of Nasabah objects.

    Steps:
      1. Build the raw decision matrix from each nasabah's attributes.
      2. Normalize the matrix:
           - Benefit criteria: value / max(column)
           - Cost criteria:    min(column) / value
      3. Compute weighted sum score for each alternative.
      4. Sort descending by final score.

    Args:
        nasabah_list: List of Nasabah ORM objects from the database.

    Returns:
        List of dicts sorted by score (highest first), each containing:
          rank, customer_id, name, raw criteria values,
          normalized criteria values, and final_score.
        Returns an empty list if input is empty.
    """
    if not nasabah_list:
        return []

    # ── Step 1: Build raw decision matrix ────────────────────
    records = []
    for n in nasabah_list:
        k1 = n.applicant_income + n.coapplicant_income   # Total income (Benefit)
        k2 = float(n.credit_history)                      # Credit history (Benefit)
        k3 = n.loan_amount                                # Loan amount (Cost)
        k4 = float(n.dependents + 1)                      # Dependents +1 avoids div/0 (Cost)
        records.append({
            'id':             n.id,
            'customer_id':    n.customer_id,
            'name':           n.name,
            # Raw criteria
            'K1_raw': k1,
            'K2_raw': k2,
            'K3_raw': k3,
            'K4_raw': k4,
            # Additional display fields
            'applicant_income':   n.applicant_income,
            'coapplicant_income': n.coapplicant_income,
            'credit_history':     n.credit_history,
            'loan_amount':        n.loan_amount,
            'dependents':         n.dependents,
        })

    # ── Step 2: Compute column extremes for normalization ────
    max_k1 = max(r['K1_raw'] for r in records)
    max_k2 = max(r['K2_raw'] for r in records)
    min_k3 = min(r['K3_raw'] for r in records)
    min_k4 = min(r['K4_raw'] for r in records)

    # Guard against zero denominators (all-zero columns)
    max_k1 = max_k1 if max_k1 != 0 else 1
    max_k2 = max_k2 if max_k2 != 0 else 1

    # ── Step 3 & 4: Normalize and score ─────────────────────
    results = []
    for r in records:
        n_k1 = r['K1_raw'] / max_k1                          # Benefit
        n_k2 = r['K2_raw'] / max_k2                          # Benefit
        n_k3 = min_k3 / r['K3_raw'] if r['K3_raw'] != 0 else 0  # Cost
        n_k4 = min_k4 / r['K4_raw'] if r['K4_raw'] != 0 else 0  # Cost

        final_score = (
            n_k1 * AHP_WEIGHTS['K1'] +
            n_k2 * AHP_WEIGHTS['K2'] +
            n_k3 * AHP_WEIGHTS['K3'] +
            n_k4 * AHP_WEIGHTS['K4']
        )

        results.append({
            **r,
            # Normalized values (4 decimal places for display)
            'N_K1': round(n_k1, 4),
            'N_K2': round(n_k2, 4),
            'N_K3': round(n_k3, 4),
            'N_K4': round(n_k4, 4),
            'final_score': round(final_score, 4),
        })

    # ── Step 5: Sort by score descending, add rank ───────────
    results.sort(key=lambda x: x['final_score'], reverse=True)
    for i, row in enumerate(results, start=1):
        row['rank'] = i

    return results


def get_criteria_meta():
    """Return criteria metadata list for template rendering."""
    return CRITERIA_META
