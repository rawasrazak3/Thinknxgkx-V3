
import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
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
        "clientCode": "ALNILE_THINKNXG_FI",
        "integrationKey": "BILLING_DUE_SETTLEMENT",
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")


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
            t_date = getdate(add_days(nowdate(), -2))

        # Get no_of_days from settings and calculate from_date
        no_of_days = cint(settings.get("no_of_days") or 3)  # default 3 days if not set
        f_date = getdate(add_days(t_date, -no_of_days))

        # Convert to timestamps (GMT+4)
        gmt_plus_4 = timezone(timedelta(hours=4))
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

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
        frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")
        # frappe.msgprint(f"[DEBUG] Received billing_data: {billing_data}")
        
        ar_details = billing_data
        bill_no = ar_details.get("bill_no")
        admission_id = ar_details.get("admissionId")
        receipt_no = ar_details.get("receipt_no")
        uhid = ar_details.get("uhId")
        payment_details = ar_details.get("payment_transaction_details", [])
        rec_amount = ar_details.get("received_amount")
        customer_name = ar_details.get("payer_name") or billing_data.get("customer")
        payer_type = ar_details.get("payer_type") or billing_data["payer_type"]
        customer = get_or_create_customer(customer_name,payer_type)
        
        # --- Fetch accounts dynamically from Company ---
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)

        debit_account = company_doc.default_receivable_account
        credit_account = company_doc.default_income_account
        cash_account = company_doc.default_cash_account
        bank_account = company_doc.default_bank_account
        frappe.logger().info(f"[JE DEBUG] Bill No: {bill_no}")
        # frappe.msgprint(f"[DEBUG] Bill No: {bill_no}")
        frappe.logger().info(f"[JE DEBUG] Customer Name: {customer_name}")
        # frappe.msgprint(f"[DEBUG] Customer Name: {customer_name}")

        if not customer_name:
            return "Failed: No customer/payer found in billing data"


        # Date conversion
        date = ar_details["g_creation_time"]
        datetimes = date / 1000.0

        # Define GMT+4
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
        formatted_date = dt.strftime('%Y-%m-%d')

        frappe.logger().info(f"[JE DEBUG] Formatted Posting Date: {formatted_date}")
        # frappe.msgprint(f"[DEBUG] Posting Date: {formatted_date}")

        # Initialize JE entries
        je_entries = []


        existing_je = frappe.db.exists(
            "Journal Entry",
            {
                "posting_date": formatted_date,
                "docstatus": 1,  # submitted
                "user_remark": f"AR Settlement for Bill No: {bill_no}"
            }
        )
        if existing_je:
            frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
            return f"Skipped: Journal Entry {existing_je} already exists"

    
        # Credit the payer
        if customer:
            # is due:true
            credit_entry = {
                "account": "Due Ledger - AN", 
                # "party_type": "Customer",
                # "party": customer,
                "credit_in_account_currency": rec_amount,
                "debit_in_account_currency": 0
            }
            je_entries.append(credit_entry)
            frappe.logger().info(f"[JE DEBUG] Added Credit Entry to Customer: {credit_entry}")
        else:
            # is due : false
            credit_entry = {
                "account": "Due Ledger - AN", 
                "debit_in_account_currency": 0,
                "credit_in_account_currency": rec_amount,
                # "party_type": "Customer",
                # "party": customer,
            }
            je_entries.append(credit_entry)
            frappe.logger().info(f"[JE DEBUG] Added Credit Entry to Due: {credit_entry}")


        #Debit each payment mode from payment_details
        for payment in payment_details:
            mode = payment.get("payment_mode_code", "").lower()
            amount = payment.get("amount", 0)

            frappe.logger().info(f"[JE DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")
            # frappe.msgprint(f"[DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")

            if amount <= 0:
                frappe.logger().warning(f"[JE DEBUG] Skipping mode {mode} as amount is 0")
                continue

            if mode == "cash":
                account = cash_account
            elif mode in ["upi", "card", "prepaid card", "credit"]:
                account = bank_account
            elif mode in ["bank transfer", "neft"]:
                account = "0429028333140012 - BANK MUSCAT - AN"
            else:
                account = bank_account

            debit_entry = {
                "account": account,
                "debit_in_account_currency": amount,
                "credit_in_account_currency": 0,
                # "party_type": "Customer",
                # "party": customer    
             }

            je_entries.append(debit_entry)
            frappe.logger().info(f"[JE DEBUG] Added Debit Entry: {debit_entry}")
            # frappe.msgprint(f"[DEBUG] Debit Entry: {debit_entry}")

        frappe.logger().info(f"[JE DEBUG] Final JE Entries: {je_entries}")
        # frappe.msgprint(f"[DEBUG] Final JE Entries: {je_entries}")

        #Create the Journal Entry
        je_doc = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "accounts": je_entries,
            "naming_series": "KX-JV-.YYYY.-",
            "user_remark": f"Due Settlement for Bill No: {bill_no}",
            "custom_bill_category": "DUE SETTLEMENT",
            "custom_bill_number": bill_no,
            "custom_uhid": uhid,
            "custom_payer_name": customer,
            "custom_receipt_no": receipt_no,
            "custom_admission_id": admission_id
        })
        je_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        je_doc.submit()
        frappe.logger().info(f"[JE DEBUG] Journal Entry {je_doc.name} created successfully.")
        # frappe.msgprint(f"[DEBUG] Journal Entry {je_doc.name} created successfully.")

        return je_doc.name

    except Exception as e:
        frappe.log_error(f"Error creating Journal Entry: {str(e)}")
        frappe.logger().error(f"[JE DEBUG] Exception: {str(e)}")
        # frappe.msgprint(f"[DEBUG] Error: {str(e)}")
        return f"Failed to create Journal Entry: {str(e)}"

def get_or_create_customer(customer_name, payer_type=None):
     # If payer type is cash, don't create a customer
    if payer_type and payer_type.lower() == "cash":
        return None

    # Determine customer group based on payer_type
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