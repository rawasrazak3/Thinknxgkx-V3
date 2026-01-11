# import frappe
# import requests
# import json
# from frappe.utils import nowdate
# from datetime import datetime
# from frappe.utils import getdate, add_days, cint
# from datetime import datetime, timedelta,timezone,time
# from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# billing_type = "PHARMACY BILLING REFUND"
# settings = frappe.get_single("Karexpert Settings")
# TOKEN_URL = settings.get("token_url")
# BILLING_URL = settings.get("billing_url")
# facility_id = settings.get("facility_id")

# # Fetch row details based on billing type
# billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
#                                 ["client_code", "integration_key", "x_api_key"], as_dict=True)

# headers_token = fetch_api_details(billing_type)


# def get_jwt_token():
#     response = requests.post(TOKEN_URL, headers=headers_token)
#     if response.status_code == 200:
#         return response.json().get("jwttoken")
#     else:
#         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

# def fetch_op_billing_refund(jwt_token, from_date, to_date):
#     headers_billing = {
#         "Content-Type": headers_token["Content-Type"],
#         "clientCode": headers_token["clientCode"],
#         "integrationKey": headers_token["integrationKey"],
#         "Authorization": f"Bearer {jwt_token}"
#     }
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch Pharmacy Refund data: {response.status_code} - {response.text}")

# def get_or_create_customer(customer_name):
#     existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name})
#     if existing_customer:
#         return existing_customer
    
#     customer = frappe.get_doc({
#         "doctype": "Customer",
#         "customer_name": customer_name,
#         "customer_group": "Individual",
#         "territory": "All Territories"
#     })
#     customer.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return customer.name

# def get_or_create_patient(patient_name,gender):
#     existing_patient = frappe.db.exists("Patient", {"patient_name": patient_name})
#     if existing_patient:
#         return existing_patient
    
#     customer = frappe.get_doc({
#         "doctype": "Patient",
#         "first_name": patient_name,
#         "sex": gender
#     })
#     customer.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return customer.name
# def get_or_create_cost_center(treating_department_name):
#     cost_center_name = f"{treating_department_name} - AN"
    
#     # Check if the cost center already exists by full name
#     existing = frappe.db.exists("Cost Center", cost_center_name)
#     if existing:
#         return cost_center_name
    
#     # Determine parent based on treating_department_name
#     if treating_department_name is not None:     # even "", null, or any value
#         parent_cost_center = "Al Nile Hospital - AN"

#     # Create new cost center with full cost_center_name as document name
#     cost_center = frappe.get_doc({
#         "doctype": "Cost Center",
#         "name": cost_center_name,               # Explicitly set doc name to full name with suffix
#         "cost_center_name": treating_department_name,  # Display name without suffix
#         "parent_cost_center": parent_cost_center,
#         "is_group": 0,
#         "company": "Al Nile Hospital"
#     })
#     cost_center.insert(ignore_permissions=True)
#     frappe.db.commit()
#     frappe.msgprint(f"Cost Center '{cost_center_name}' created under '{parent_cost_center}'")
    
#     return cost_center_name  # Always return the full cost center name with suffix

# @frappe.whitelist()
# def main():
#     try:
#         jwt_token = get_jwt_token()
#         frappe.log("JWT Token fetched successfully.")

#         # from_date = 1672531200000  
#         # to_date = 1940009600000    
#         # Fetch dynamic date and number of days from settings
#         settings = frappe.get_single("Karexpert Settings")
#         # Get to_date from settings or fallback to nowdate() - 4 days
#         to_date_raw = settings.get("date")
#         if to_date_raw:
#             t_date = getdate(to_date_raw)
#         else:
#             t_date = add_days(nowdate(), -4)

#         # Get no_of_days from settings and calculate from_date
#         no_of_days = cint(settings.get("no_of_days") or 25)  # default 3 days if not set
#         f_date = add_days(t_date, -no_of_days)
#          # Define GMT+4 timezone
#         gmt_plus_4 = timezone(timedelta(hours=4))

#         # Convert to timestamps in milliseconds for GMT+4
#         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
#         print("---f", from_date)
#         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
#         print("----t", to_date)
#         billing_data = fetch_op_billing_refund(jwt_token, from_date, to_date)
#         frappe.log("Pharmacy Billing refund data fetched successfully.")

#         for billing in billing_data.get("jsonResponse", []):
#             create_journal_entry_from_pharmacy_refund(billing["pharmacy_refund"])

#     except Exception as e:
#         frappe.log_error(f"Error: {e}")

# if __name__ == "__main__":
#     main()

# def create_journal_entry_from_pharmacy_refund(refund_data):
#     bill_no = refund_data["bill_no"]
#     receipt_no = refund_data.get("receipt_no")

#     payment_details = refund_data.get("payment_transaction_details", [])
#     date = refund_data["g_creation_time"]
#     datetimes = date / 1000.0

#     # Define GMT+4
#     gmt_plus_4 = timezone(timedelta(hours=4))
#     dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
#     formatted_date = dt.strftime('%Y-%m-%d')
#     posting_time = dt.strftime('%H:%M:%S')

#     if frappe.db.exists("Journal Entry", {"custom_bill_number": bill_no, "docstatus": ["!=", 2] ,"custom_bill_category": "PHARMACY REFUND"}):
#         frappe.log(f"Refund Journal Entry with bill_no {bill_no} already exists.")
#         return

#     # Patient & Customer
#     customer_name = refund_data["payer_name"]
#     payer_type = refund_data["payer_type"]
#     patient_name = refund_data["patient_name"]
#     gender = refund_data["patient_gender"]

#     customer = get_or_create_customer(customer_name)
#     patient = get_or_create_patient(patient_name, gender)

#     treating_department_name = refund_data.get("treating_department_name", "Default Dept")
#     cost_center = get_or_create_cost_center(treating_department_name)

#     # Amounts (Refund)
#     item_rate = refund_data["patient_refund_amount"]
#     tax_amount = refund_data.get("tax", 0)
#     authorized_amount = refund_data.get("authorized_amount", 0)
#     discount_amount = refund_data.get("selling_amount", 0) - refund_data.get("total_amount", 0)

#     # --- Fetch accounts dynamically from Company ---
#     company = frappe.defaults.get_user_default("Company")
#     company_doc = frappe.get_doc("Company", company)

#     credit_account = company_doc.default_income_account     # opposite of billing
#     debit_account = company_doc.default_receivable_account
#     cash_account = company_doc.default_cash_account
#     bank_account = company_doc.default_bank_account
#     card_account = company_doc.default_bank_account
#     vat_account = "Output VAT 5% - AN"
#     default_expense_account = company_doc.default_expense_account
#     default_stock_in_hand = company_doc.default_inventory_account
#     if payer_type.lower() == "cash":
#         customer_advance_account = "Advance Received - AN"
#     else:
#         customer_advance_account = "Debtors - AN"

#     total_uepr = sum(
#         (item.get("ueprValue") or 0)
#         for item in refund_data.get("item_details", [])
#     )

#     original_jv = frappe.get_all(
#         "Journal Entry",
#         filters={"custom_bill_number": bill_no, "docstatus": 1,"custom_bill_category": "PHARMACY"},
#         fields=["name"],
#         limit=1
#     )
#     reference_invoice = original_jv[0]["name"] if original_jv else None
#     if not reference_invoice:
#         frappe.log(f"No original pharmacy Journal found with bill No: {bill_no}")
#     total_uepr = sum(
#         (item.get("ueprValue") or 0)
#         for item in refund_data.get("item_details", [])
#     )

#     # je_accounts = [
#     #     {
#     #         "account": debit_account,   # Reverse sales (debit sales account)
#     #         "debit_in_account_currency": item_rate,
#     #         "credit_in_account_currency": 0,
#     #         "cost_center": cost_center
#     #     },
#     #     {
#     #         "account": credit_account,  # Credit receivable/customer
#     #         "debit_in_account_currency": item_rate,
#     #         "credit_in_account_currency": 0,
#     #         "cost_center": cost_center,
#     #         # "reference_type": "Journal Entry",
#     #         # "reference_name": reference_invoice

#     #         # "party_type": "Customer",
#     #         # "party": customer
#     #     },
#     # ]

#     je_accounts = [
#         # Reverse income
#         {
#             "account": credit_account,   # Income
#             "debit_in_account_currency": item_rate,
#             "credit_in_account_currency": 0,
#             "cost_center": cost_center,
#             "reference_type": "Journal Entry",
#             "reference_name": reference_invoice
#         },
#         # Reverse receivable
#         # {
#         #     "account": debit_account,    # Debtors
#         #     "debit_in_account_currency": 0,
#         #     "credit_in_account_currency": item_rate,
#         #     "cost_center": cost_center,
#         #     "party_type": "Customer",
#         #     "party": customer
#         # },
#     ]

#     # Tax reversal
#     if tax_amount > 0:
#         je_accounts.append({
#             "account": vat_account,
#             "debit_in_account_currency": tax_amount,
#             "credit_in_account_currency": 0,
#             "cost_center": cost_center,
#             # "reference_type": "Journal Entry",
#             # "reference_name": reference_invoice
#         })

#     # UEPR reversal
#     if total_uepr > 0:
#         je_accounts.extend([
#             {
#                 "account": default_stock_in_hand,
#                 "debit_in_account_currency": total_uepr,
#                 "credit_in_account_currency": 0,
#                 "cost_center": cost_center,
#                 # "reference_type": "Journal Entry",
#                 # "reference_name": reference_invoice,
#             },
#             {
#                 "account": default_expense_account,
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": total_uepr,
#                 "cost_center": cost_center,
#                 # "reference_type": "Journal Entry",
#                 # "reference_name": reference_invoice,
#             }
#         ])

#     # Payment Modes (Refunds)
#     for payment in payment_details:
#         mode = payment["payment_mode_code"].lower()
#         amount = payment.get("amount", 0.0)
#         if amount <= 0:
#             continue

#         if mode == "cash":
#             je_accounts.append({
#                 "account": cash_account,
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": amount,
#                 # "reference_type": "Journal Entry",
#                 # "reference_name": reference_invoice
#             })
#         elif mode == "credit":
#             je_accounts.append({
#                 "account": debit_account,
#                 "debit_in_account_currency":0,
#                 "credit_in_account_currency":amount,
#                 "party_type": "Customer",
#                 "party": customer,
#                 "reference_type": "Journal Entry",
#                 "reference_name": reference_invoice
#             })
#         elif mode in ["upi", "card_payment", "bank", "neft"]:
#             je_accounts.append({
#                 "account": bank_account,
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": amount,
#                 # "reference_type": "Journal Entry",
#                 # "reference_name": reference_invoice
#             })
#         elif mode in ["ip advance", "uhid_advance"]:
#             je_accounts.append({
#                 "account": "Advance Received - AN",
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": amount,
#                 # "reference_type": "Journal Entry",
#                 # "reference_name": reference_invoice
#             })

#     # --- Create Refund JE ---
#     je = frappe.get_doc({
#         "doctype": "Journal Entry",
#         "naming_series": "KX-JV-.YYYY.-",
#         "voucher_type": "Journal Entry",
#         "posting_date": formatted_date,
#         "posting_time": posting_time,
#         "custom_patient_name": patient_name,
#         "custom_patient": patient_name,
#         "custom_bill_number": bill_no,
#         "custom_bill_category": "PHARMACY REFUND",
#         "custom_payer_name": customer_name,
#         "custom_uhid": refund_data["uhId"],
#         "custom_receipt_no": receipt_no,
#         "custom_admission_id": refund_data["admissionId"],
#         "custom_admission_type": refund_data["admissionType"],
#         "company": company,
#         "user_remark": f"Pharmacy Refund for bill no {bill_no}",
#         "accounts": je_accounts
#     })

#     try:
#         je.insert(ignore_permissions=True)
#         je.submit()
#         frappe.db.commit()
#         frappe.log(f"Refund Journal Entry created successfully with bill_no: {bill_no}")
#         return je.name
#     except Exception as e:
#         frappe.log_error(f"Failed to create refund Journal Entry: {e}")
#         return None

import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta,timezone,time
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "PHARMACY BILLING REFUND"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)

headers_token = fetch_api_details(billing_type)


def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

def fetch_op_billing_refund(jwt_token, from_date, to_date):
    headers_billing = {
        "Content-Type": headers_token["Content-Type"],
        "clientCode": headers_token["clientCode"],
        "integrationKey": headers_token["integrationKey"],
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch Pharmacy Refund data: {response.status_code} - {response.text}")

def get_or_create_customer(customer_name, payer_type=None):
    # existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name})
    # if existing_customer:
    #     return existing_customer
    
    # customer = frappe.get_doc({
    #     "doctype": "Customer",
    #     "customer_name": customer_name,
    #     "customer_group": "Individual",
    #     "territory": "All Territories"
    # })
    if payer_type and payer_type.lower() == "cash":
        return None
    # Check if the customer already exists
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":payer_type})
    if existing_customer:
        return existing_customer

    # Determine customer group based on payer_type
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "insurance":
            customer_group = "Insurance"
        elif payer_type == "cash":
            customer_group = "Cash"
        elif payer_type == "corporate":
            customer_group = "Corporate"
        elif payer_type == "credit":
            customer_group = "Credit"
        else:
            customer_group = "Individual"  # default fallback
    else:
        customer_group = "Individual"

    # Create new customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_group": customer_group,
        "territory": "All Territories"
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()
    return customer.name

def get_or_create_patient(patient_name,gender):
    existing_patient = frappe.db.exists("Patient", {"patient_name": patient_name})
    if existing_patient:
        return existing_patient
    
    customer = frappe.get_doc({
        "doctype": "Patient",
        "first_name": patient_name,
        "sex": gender
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()
    return customer.name
def get_or_create_cost_center(treating_department_name):
    cost_center_name = f"{treating_department_name} - AN"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Cost Center", cost_center_name)
    if existing:
        return cost_center_name
    
    # Determine parent based on treating_department_name
    if treating_department_name is not None:     # even "", null, or any value
        parent_cost_center = "Al Nile Hospital - AN"

    # Create new cost center with full cost_center_name as document name
    cost_center = frappe.get_doc({
        "doctype": "Cost Center",
        "name": cost_center_name,               # Explicitly set doc name to full name with suffix
        "cost_center_name": treating_department_name,  # Display name without suffix
        "parent_cost_center": parent_cost_center,
        "is_group": 0,
        "company": "Al Nile Hospital"
    })
    cost_center.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Cost Center '{cost_center_name}' created under '{parent_cost_center}'")
    
    return cost_center_name  # Always return the full cost center name with suffix

@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # from_date = 1672531200000  
        # to_date = 1940009600000    
        # Fetch dynamic date and number of days from settings
        settings = frappe.get_single("Karexpert Settings")
        # Get to_date from settings or fallback to nowdate() - 4 days
        to_date_raw = settings.get("date")
        if to_date_raw:
            t_date = getdate(to_date_raw)
        else:
            t_date = add_days(nowdate(), -4)

        # Get no_of_days from settings and calculate from_date
        no_of_days = cint(settings.get("no_of_days") or 25)  # default 3 days if not set
        f_date = add_days(t_date, -no_of_days)
         # Define GMT+4 timezone
        gmt_plus_4 = timezone(timedelta(hours=4))

        # Convert to timestamps in milliseconds for GMT+4
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        print("---f", from_date)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
        print("----t", to_date)
        billing_data = fetch_op_billing_refund(jwt_token, from_date, to_date)
        frappe.log("Pharmacy Billing refund data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry_from_pharmacy_refund(billing["pharmacy_refund"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

def create_journal_entry_from_pharmacy_refund(refund_data):
    bill_no = refund_data["bill_no"]
    receipt_no = refund_data.get("receipt_no")

    payment_details = refund_data.get("payment_transaction_details", [])
    date = refund_data["g_creation_time"]
    datetimes = date / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    formatted_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')

    if frappe.db.exists("Journal Entry", {"custom_bill_number": bill_no, "docstatus": ["!=", 2] ,"custom_bill_category": "PHARMACY REFUND"}):
        frappe.log(f"Refund Journal Entry with bill_no {bill_no} already exists.")
        return

    # Patient & Customer
    customer_name = refund_data["payer_name"]
    payer_type = refund_data["payer_type"]
    patient_name = refund_data["patient_name"]
    gender = refund_data["patient_gender"]

    customer = get_or_create_customer(customer_name)
    patient = get_or_create_patient(patient_name, gender)

    treating_department_name = refund_data.get("treating_department_name", "Default Dept")
    cost_center = get_or_create_cost_center(treating_department_name)

    # Amounts (Refund)
    item_rate = refund_data["taxable_amount"]
    tax_amount = refund_data.get("tax", 0)
    authorized_amount = refund_data.get("authorized_amount", 0)
    discount_amount = refund_data.get("selling_amount", 0) - refund_data.get("taxable_amount", 0)

    # --- Fetch accounts dynamically from Company ---
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company)

    credit_account = company_doc.default_income_account     # opposite of billing
    debit_account = company_doc.default_receivable_account
    cash_account = company_doc.default_cash_account
    bank_account = company_doc.default_bank_account
    card_account = company_doc.default_bank_account
    vat_account = "VAT 5% - AN"
    default_expense_account = company_doc.default_expense_account
    default_stock_in_hand = company_doc.default_inventory_account
    if payer_type.lower() == "cash":
        customer_advance_account = "Advance Received - AN"
    else:
        customer_advance_account = "Debtors - AN"

    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in refund_data.get("item_details", [])
    )

    original_jv = frappe.get_all(
        "Journal Entry",
        filters={"custom_bill_number": bill_no, "docstatus": 1,"custom_bill_category": "PHARMACY"},
        fields=["name"],
        limit=1
    )
    reference_invoice = original_jv[0]["name"] if original_jv else None
    if not reference_invoice:
        frappe.log(f"No original pharmacy Journal found with bill No: {bill_no}")
    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in refund_data.get("item_details", [])
    )

    # je_accounts = [
    #     {
    #         "account": debit_account,   # Reverse sales (debit sales account)
    #         "debit_in_account_currency": item_rate,
    #         "credit_in_account_currency": 0,
    #         "cost_center": cost_center
    #     },
    #     {
    #         "account": credit_account,  # Credit receivable/customer
    #         "debit_in_account_currency": item_rate,
    #         "credit_in_account_currency": 0,
    #         "cost_center": cost_center,
    #         # "reference_type": "Journal Entry",
    #         # "reference_name": reference_invoice

    #         # "party_type": "Customer",
    #         # "party": customer
    #     },
    # ]

    je_accounts = [
        # Reverse income
        {
            "account": credit_account,   # Income
            "debit_in_account_currency": item_rate,
            "credit_in_account_currency": 0,
            "cost_center": cost_center,
            "reference_type": "Journal Entry",
            "reference_name": reference_invoice
        },
        # Reverse receivable
        {
            "account": debit_account,    # Debtors
            "debit_in_account_currency": 0,
            "credit_in_account_currency": item_rate,
            "cost_center": cost_center,
            "party_type": "Customer",
            "party": customer
        },
    ]

    # Tax reversal
    if tax_amount > 0:
        je_accounts.append({
            "account": vat_account,
            "debit_in_account_currency": tax_amount,
            "credit_in_account_currency": 0,
            "cost_center": cost_center,
            # "reference_type": "Journal Entry",
            # "reference_name": reference_invoice
        })

    # UEPR reversal
    if total_uepr > 0:
        je_accounts.extend([
            {
                "account": default_stock_in_hand,
                "debit_in_account_currency": total_uepr,
                "credit_in_account_currency": 0,
                "cost_center": cost_center,
                # "reference_type": "Journal Entry",
                # "reference_name": reference_invoice,
            },
            {
                "account": default_expense_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": total_uepr,
                "cost_center": cost_center,
                # "reference_type": "Journal Entry",
                # "reference_name": reference_invoice,
            }
        ])

    # Payment Modes (Refunds)
    for payment in payment_details:
        mode = payment["payment_mode_code"].lower()
        amount = payment.get("amount", 0.0)
        if amount <= 0:
            continue

        if mode == "cash":
            je_accounts.append({
                "account": cash_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                # "reference_type": "Journal Entry",
                # "reference_name": reference_invoice
            })
        elif mode in ["credit", "prepaid card"]:
            je_accounts.append({
                "account": debit_account,
                "debit_in_account_currency":0,
                "credit_in_account_currency":amount,
                "party_type": "Customer",
                "party": customer,
                "reference_type": "Journal Entry",
                "reference_name": reference_invoice
            })
        elif mode in ["upi", "card_payment", "bank", "neft"]:
            je_accounts.append({
                "account": bank_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                # "reference_type": "Journal Entry",
                # "reference_name": reference_invoice
            })
        elif mode in ["ip advance", "uhid_advance"]:
            je_accounts.append({
                "account": "Advance Received - AN",
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                # "reference_type": "Journal Entry",
                # "reference_name": reference_invoice
            })

    # --- Create Refund JE ---
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "naming_series": "KX-JV-.YYYY.-",
        "voucher_type": "Journal Entry",
        "posting_date": formatted_date,
        "posting_time": posting_time,
        "custom_patient_name": patient_name,
        "custom_patient": patient_name,
        "custom_bill_number": bill_no,
        "custom_bill_category": "PHARMACY REFUND",
        "custom_payer_name": customer_name,
        "custom_uhid": refund_data["uhId"],
        "custom_receipt_no": receipt_no,
        "custom_admission_id": refund_data["admissionId"],
        "custom_admission_type": refund_data["admissionType"],
        "company": company,
        "user_remark": f"Pharmacy Refund for bill no {bill_no}",
        "accounts": je_accounts
    })

    try:
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.db.commit()
        frappe.log(f"Refund Journal Entry created successfully with bill_no: {bill_no}")
        return je.name
    except Exception as e:
        frappe.log_error(f"Failed to create refund Journal Entry: {e}")
        return None