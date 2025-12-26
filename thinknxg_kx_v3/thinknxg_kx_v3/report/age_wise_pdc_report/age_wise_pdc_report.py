# Copyright (c) 2025, thinknxg and contributors
# For license information, please see license.txt


import frappe
from frappe.utils import nowdate, date_diff

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Payment Entry", "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 200},
        {"label":"Party","fieldname":"party","fieldtype":"Data","width":150},
        {"label": "Payment Type", "fieldname": "payment_type", "fieldtype": "Data", "width": 100},
        
        {"label": "Cheque No", "fieldname": "reference_no", "fieldtype": "Data", "width": 150},
        {"label": "Cheque Date", "fieldname": "reference_date", "fieldtype": "Date", "width": 150},
        # {"label": "Cheque Issue", "fieldname": "custom_cheque_issue_date", "fieldtype": "Date", "width": 120},
        
        {"label":"Remarks","fieldname":"remarks","fieldtype":"Data","width":150},
        {"label": "Amount", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Mode of Payment", "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 150},
        {"label": "Age (Days)", "fieldname": "age", "fieldtype": "Int", "width": 100},
        {"label": "Age Bucket", "fieldname": "age_bucket", "fieldtype": "Data", "width": 120}
        
        
    ]

def get_data(filters):
    frappe.flags.ignore_cache = True
    # Conditions based on user inputs
    conditions = []

    # Apply filters based on user input
    if filters.get("party_type"):
        conditions.append("pe.party_type = %(party_type)s")
    if filters.get("party"):
        conditions.append("pe.party = %(party)s")
    if filters.get("payment_type"):
        conditions.append("pe.payment_type = %(payment_type)s")


    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("pe.reference_date BETWEEN %(from_date)s AND %(to_date)s")

    # Join conditions with 'AND'
    conditions = " AND ".join(conditions)

    if conditions:
        conditions = " AND " + conditions

    # Fetch filtered payment entries
    pdc_entries = frappe.db.sql(f"""
        SELECT
            pe.name AS payment_entry,
            pe.party,
            pe.party_name,
            pe.payment_type,
            pe.reference_no,
            pe.reference_date,
            pe.paid_amount,
            pe.mode_of_payment,
            # pe.custom_cheque_issue_date,
            pe.remarks
        FROM
            `tabPayment Entry` pe
        WHERE
            pe.docstatus = 1
            AND pe.mode_of_payment IN ('Cheque BM', 'Cheque NBO', 'Bank Transfer NBO', 'Bank Transfer BM')
            AND pe.reference_date IS NOT NULL
            {conditions}
        ORDER BY
            pe.reference_date ASC
    """, filters, as_dict=1)

    # Process the data and calculate age
    data = []
    for entry in pdc_entries:
        age = date_diff( entry.reference_date ,nowdate())

        # Define age buckets
        if age <= 30:
            age_bucket = '0-30 Days'
        elif 31 <= age <= 60:
            age_bucket = '31-60 Days'
        elif 61 <= age <= 90:
            age_bucket = '61-90 Days'
        else:
            age_bucket = '90+ Days'

        # Append data to the list
        data.append({
            "payment_entry": entry.payment_entry,
            "party": entry.party,
            "party_name": entry.party_name,
            "payment_type": entry.payment_type,
            "reference_no": entry.reference_no,
            "reference_date": entry.reference_date,
            # "custom_cheque_issue_date":entry.custom_cheque_issue_date,
            "remarks": entry.remarks,
            "paid_amount": entry.paid_amount,
            "mode_of_payment": entry.mode_of_payment,
            "age": age,
            "age_bucket": age_bucket
        })

    return data
