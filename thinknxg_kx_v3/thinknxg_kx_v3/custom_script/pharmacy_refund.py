
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
     # If payer type is cash, don't create a customer
    if payer_type and payer_type.lower() == "cash":
        return None
     
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "insurance":
            customer_group = "Insurance"
        elif payer_type == "corporate":
            customer_group = "Corporate"
        elif payer_type == "cash":
            customer_group = "Cash"
        elif payer_type == "tpa":
            customer_group = "TPA"
        elif payer_type == "credit":
            customer_group = "Credit"
        else:
            customer_group = "Cash"  # default fallback
    else:
        customer_group = "Cash"  # default if payer_type is None

    # Check if the customer already exists
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":customer_group})
    if existing_customer:
        return existing_customer
    
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


def get_or_create_cost_center(department):
    # company = "Al Nile Hospital"
    # company_default_cc = frappe.db.get_value(
    #     "Company",
    #     company,
    #     "cost_center"
    # )
    
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company)

    company_default_cc = company_doc.cost_center

    if not department:
        return company_default_cc

    cost_center_name = f"{department} - AN"

    if frappe.db.exists("Cost Center", cost_center_name):
        return cost_center_name

    parent_cost_center = company_default_cc

    # Create new cost center
    cost_center = frappe.get_doc({
        "doctype": "Cost Center",
        "name": cost_center_name,                 
        "cost_center_name": department,  
        "parent_cost_center": parent_cost_center,
        "is_group": 0,
        "company": company
    })

    cost_center.insert(ignore_permissions=True)
    frappe.db.commit()

    frappe.msgprint(
        f"Cost Center '{cost_center_name}' created under '{parent_cost_center}'"
    )

    return cost_center_name




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
    modification_time = refund_data.get("g_modification_time", date)  # fallback if not present
    mod_date = modification_time / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    formatted_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')
    mod_dt = datetime.fromtimestamp(mod_date, gmt_plus_4)
    mod_time = mod_dt.strftime('%Y-%m-%d %H:%M:%S')


    existing_jv = frappe.db.get_value(
        "Journal Entry",
        {"custom_receipt_no": receipt_no, "docstatus": ["!=", 2] ,"custom_bill_category": "PHARMACY REFUND"},
        ["name", "custom_modification_time"],
        as_dict=True
    )

    if existing_jv:
        stored_mod_time = existing_jv.get("custom_modification_time")
        if stored_mod_time and str(stored_mod_time) == str(mod_time):
            frappe.log(f"Journal Entry {bill_no} already up-to-date. Skipping...")
            return existing_jv["name"]

        # Cancel old invoice + related journals
        je_doc = frappe.get_doc("Journal Entry", existing_jv["name"])
        try:
            # # Cancel linked journals
            journals = frappe.get_all("Journal Entry",
                filters={"custom_bill_number": bill_no, "docstatus": 1},
                pluck="name")
            for jn in journals:
                je_doc = frappe.get_doc("Journal Entry", jn)
                je_doc.cancel()
                frappe.db.commit()
                frappe.log(f"Cancelled JE {jn} for bill {bill_no}")

            # Cancel invoice
            je_doc.reload()
            je_doc.cancel()
            frappe.db.commit()
            frappe.log(f"Cancelled JV {existing_jv['name']} for modified bill {bill_no}")
        except Exception as e:
            frappe.log_error(f"Error cancelling JE for bill {bill_no}: {e}")
            return None

    if frappe.db.exists("Journal Entry", {"custom_receipt_no": receipt_no, "docstatus": ["!=", 2] ,"custom_bill_category": "PHARMACY REFUND"}):
        frappe.log(f"Refund Journal Entry with bill_no {bill_no} already exists.")
        return
    


    # Patient & Customer
    customer_name = refund_data["payer_name"]
    payer_type = refund_data["payer_type"]
    patient_name = refund_data["patient_name"]
    gender = refund_data["patient_gender"]

    customer = get_or_create_customer(customer_name, payer_type)
    patient = get_or_create_patient(patient_name, gender)

    department = refund_data.get("department")
    cost_center = get_or_create_cost_center(department)

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
    reference_invoice = None
    original_cost_center = None

    if original_jv:
        reference_invoice = original_jv[0]["name"]

        original_cost_center = frappe.db.get_value(
            "Journal Entry Account",
            {
                "parent": reference_invoice,
                "cost_center": ["is", "set"]
            },
            "cost_center"
        )
        if original_cost_center:
            cost_center = original_cost_center
        else:
            department = refund_data.get("department")
            cost_center = get_or_create_cost_center(department)


        original_debtors_cc = None

        if reference_invoice:
            original_debtors_cc = frappe.db.get_value(
                "Journal Entry Account",
                {
                    "parent": reference_invoice,
                    "party_type": "Customer",
                    "credit_in_account_currency": [">", 0]
                },
                "cost_center"
            )

        debtors_cost_center = original_debtors_cc 

    reference_invoice = original_jv[0]["name"] if original_jv else None
    if not reference_invoice:
        frappe.log(f"No original pharmacy Journal found with bill No: {bill_no}")


    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in refund_data.get("item_details", [])
    )

    je_accounts = [
        # Reverse income
        {
            "account": credit_account,   # Income
            "debit_in_account_currency": item_rate,
            "credit_in_account_currency": 0,
            "cost_center": cost_center,
            "reference_type": "Journal Entry" if reference_invoice else None,
            "reference_name": reference_invoice
        },
        # Reverse receivable
        {
            "account": debit_account,    # Debtors
            "debit_in_account_currency": 0,
            "credit_in_account_currency": item_rate,
            "cost_center": debtors_cost_center,
            "party_type": "Customer",
            "party": customer,
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
        elif mode in ["credit"]:
            je_accounts.append({
                "account": debit_account,
                "debit_in_account_currency":0,
                "credit_in_account_currency":amount,
                "party_type": "Customer",
                "party": customer,
            })
        elif mode in ["upi", "card_payment", "prepaid card"]:
            je_accounts.append({
                "account": bank_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                # "reference_type": "Journal Entry",
                # "reference_name": reference_invoice
            })
        elif mode in ["bank transfer", "neft"]:
            je_accounts.append({
                "account": "0429028333140012 - BANK MUSCAT - AN",
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
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
        "custom_modification_time": mod_time,
        "custom_patient_name": patient_name,
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