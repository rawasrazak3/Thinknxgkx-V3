import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta,time,timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "DUE SETTLEMENT"
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

def fetch_advance_billing(jwt_token, from_date, to_date):
    headers_billing = {
        "Content-Type": "application/json",
        "clientCode": "METRO_THINKNXG_FI",
        "integrationKey": "BILLING_DUE_SETTLEMENT",
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to due settlement data: {response.status_code} - {response.text}")
@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # from_date = 1672531200000  
        # to_date = 1966962420000    
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

        billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
        frappe.log("Due settlement data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry(billing["due_settlement"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

def create_journal_entry(billing_data):
    try:
        bill_no = billing_data["bill_no"]

        payment_details = billing_data.get("payment_transaction_details", [])
        
        # --- Fetch accounts dynamically from Company ---
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)

        debit_account = company_doc.default_receivable_account
        credit_account = company_doc.default_income_account
        cash_account = company_doc.default_cash_account
        bank_account = company_doc.default_bank_account
        write_off_account = company_doc.write_off_account

        authorized_amount = billing_data.get("authorized_amount", 0)
        payer_amounts = billing_data.get("received_amount", 0)
        payer_amount = authorized_amount + payer_amounts

        # Initialize journal entry rows
        je_entries = []
        je_entries.append({
                "account": "Due Ledger - AN",
                "debit_in_account_currency": 0,
                "credit_in_account_currency": payer_amount,
            })
        # Handling Credit Payment Mode
        credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
        if authorized_amount>0:
            je_entries.append({
                "account": "Debtors - AN",  # Replace with actual debtors account
                "debit_in_account_currency": authorized_amount,
                "credit_in_account_currency": 0,
            })
            

        # Handling Cash Payment Mode
        for payment in payment_details:
            if payment["payment_mode_code"].lower() == "cash":
                je_entries.append({
                    "account": cash_account,  # Replace with actual cash account
                    "debit_in_account_currency": payment["amount"],
                    "credit_in_account_currency": 0
                })

        # Handling Other Payment Modes (UPI, Card, etc.)
        bank_payment_total = sum(
            p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "credit","IP ADVANCE"]
        )
        if bank_payment_total > 0:
            je_entries.append({
                "account": bank_account,  # Replace with actual bank account
                "debit_in_account_currency": bank_payment_total,
                "credit_in_account_currency": 0
            })

        # Create Journal Entry if there are valid transactions
        if je_entries:
            je_doc = frappe.get_doc({
                "doctype": "Journal Entry",
                "posting_date": nowdate(),
                "accounts": je_entries,
                "user_remark": f"Due Settlement of: {bill_no}"
            })
            je_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            # Link Journal Entry to Sales Invoice
            # frappe.db.set_value("Sales Invoice", sales_invoice_name, "journal_entry", je_doc.name)
            frappe.msgprint(f"Journal Entry {je_doc.name} created successfully.")
    
    except Exception as e:
        frappe.log_error(f"Error creating Journal Entry: {str(e)}")
        return f"Failed to create Journal Entry: {str(e)}"

