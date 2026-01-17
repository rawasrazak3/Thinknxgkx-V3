import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, timezone,time
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "ADVANCE DEPOSIT"
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
        frappe.throw(f"Failed to fetch Advance deposit data: {response.status_code} - {response.text}")


@frappe.whitelist()
def main():
    try:
        # jwt_token = get_jwt_token()
        # frappe.log("JWT Token fetched successfully.")

        # from_date = 1752148536000  
        # to_date =  1753941033000

        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # Fetch dynamic date and number of days from settings
        settings = frappe.get_single("Karexpert Settings")
        # Get to_date from settings or fallback to nowdate() - 4 days
        to_date_raw = settings.get("date")
        if to_date_raw:
            to_date = getdate(to_date_raw)
        else:
            to_date = add_days(nowdate(), -4)

        # Get no_of_days from settings and calculate from_date
        no_of_days = cint(settings.get("no_of_days") or 3)  # default 3 days if not set
        from_date = add_days(to_date, -no_of_days)
        # Define GMT+4 timezone
        gmt_plus_4 = timezone(timedelta(hours=4))

        # Convert to timestamps in milliseconds for GMT+4
        from_date = int(datetime.combine(from_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(to_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)



        billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
        frappe.log("Advance Billing data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry(billing["advance"])
            # create_payment_entry(billing["advance"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()
def create_journal_entry(billing_data):
    print("creating journal----")
    try:
        # mode_of_payment = billing_data["payment_transaction_details"][0]["payment_mode_display"]
        # --- Fetch accounts dynamically from Company ---
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)

        debit_account = company_doc.default_receivable_account
        credit_account = company_doc.default_income_account
        cash_account = company_doc.default_cash_account
        bank_account = company_doc.default_bank_account
        card_account = company_doc.default_bank_account

        # Use fixed account based on mode of payment
        # if mode_of_payment.lower() == "Cash":
        #     print("mode is cash---")
        #     paid_to_account = cash_account
        # elif mode_of_payment.lower() == "Bank Transfer":
        #     print("mode is bank---")
        #     paid_to_account = bank_account
        # else:
        #     print("mode is card---")      #Card Payment
        #     paid_to_account = card_account

        mode_of_payment = (billing_data["payment_transaction_details"][0]
                   .get("payment_mode_display") or "").lower().strip()

        if mode_of_payment == "cash":
            paid_to_account = cash_account
        elif mode_of_payment in ("Card Payment"):
            paid_to_account = card_account
        else:
            paid_to_account = bank_account



        # Get currency of the account
        paid_to_account_currency = frappe.db.get_value("Account", paid_to_account, "account_currency")

        # mode_of_payment_accounts = frappe.get_all(
        #     "Mode of Payment Account",
        #     filters={"parent": mode_of_payment},
        #     fields=["default_account"],
        #     limit=1
        # )
        # print("MOP Acc",mode_of_payment_accounts)
        # if not mode_of_payment_accounts:
        #     print("Failed: No default account found for mode of payment")
        #     return f"Failed: No default account found for mode of payment {mode_of_payment}"

        # paid_to_account = mode_of_payment_accounts[0]["default_account"]
        # paid_to_account_currency = frappe.db.get_value("Account", paid_to_account, "account_currency")

        transaction_date_time = billing_data["payment_transaction_details"][0].get("transaction_date_time")
        if not transaction_date_time:
            print("Failed: Transaction Date is missing.")
            return "Failed: Transaction Date is missing."

        # Define GMT+4 offset
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(transaction_date_time / 1000.0, gmt_plus_4)
        formatted_date = dt.strftime('%Y-%m-%d')

        reference_no = billing_data.get("receipt_no")
        if not reference_no:
            print("Failed: Reference No is missing.")
            return "Failed: Reference No is missing."

        existing_je = frappe.get_value(
            "Journal Entry",
            {
                "custom_bill_number": reference_no
            },
            "name"
        )

        if frappe.db.exists("Journal Entry", {"custom_bill_number": reference_no,"custom_bill_category": "UHID Advance","docstatus":1}):
            print("jv exists",reference_no)
            return f"Skipped: Journal Entry already exists."

    
        transaction_id = ""
        for tx in billing_data.get("payment_transaction_details", []):
            if tx.get("transaction_id"):
                transaction_id = tx.get("transaction_id")
                break
        # frappe.log_error("Transaction ID: " + str(transaction_id), "Advance Billing Log")


        # # Check for existing Journal Entry
        # existing_je = frappe.get_value(
        #     "Journal Entry",
        #     {"cheque_no": reference_no, "posting_date": formatted_date},
        #     "name"
        # )
        # if existing_je:
        #     return f"Skipped: Journal Entry {existing_je} already exists."

        transfer_to_uhId_advance = billing_data.get("transfer_to_uhId_advance")
        customer_name = billing_data.get("payer_name")
        payer_type = billing_data.get("payer_type")
        customer = get_or_create_customer(customer_name,payer_type)
        custom_advance_type = billing_data.get("advance_type")
        custom_patient_type = billing_data.get("patient_type_display")
        custom_uhid = billing_data.get("uhId")
        amount = billing_data.get("amount")
        authorized_amount = billing_data.get("authorized_amount")
        patient_name = billing_data.get("patient_name")

        # Fetch default receivable account or use a custom "Customer Advances" account
        # customer_advance_account = frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_receivable_account")
        # if payer_type.lower() == "cash":
        #     customer_advance_account = "Advance Received - AN"
        # else:
        #             customer_advance_account = "Debtors - AN"
        payer = (payer_type or "").lower().strip()
        authorized_amount = float(authorized_amount or 0)

        if authorized_amount <= 0:
            customer_advance_account = "Advance Received - AN"
        else:
            customer_advance_account = "Debtors - AN"


        # Decide accounts based on transfer_to_uhid
        accounts = []

        if transfer_to_uhId_advance:
            # REVERSE ENTRY
            # Debit → Advance Received / Debtors
            # Credit → Cash / Bank

            accounts.append({
                "account": customer_advance_account,
                "debit_in_account_currency": amount,
                "account_currency": paid_to_account_currency,
                # "party_type": "Customer" if customer else None,
                # "party": customer,
                "is_advance": "Yes"
            })

            accounts.append({
                "account": paid_to_account,
                "credit_in_account_currency": amount,
                "account_currency": paid_to_account_currency
            })

        else:
            #  NORMAL ENTRY
            # Debit → Cash / Bank
            # Credit → Advance Received / Debtors

            accounts.append({
                "account": paid_to_account,
                "debit_in_account_currency": amount,
                "account_currency": paid_to_account_currency
            })

            accounts.append({
                "account": customer_advance_account,
                "credit_in_account_currency": amount,
                "account_currency": paid_to_account_currency,
                # "party_type": "Customer" if customer else None,
                # "party": customer,
                "is_advance": "Yes"
            })

        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "naming_series": "KX-JV-.YYYY.-",
            "posting_date": formatted_date,
            "custom_bill_number": reference_no,
            # "cheque_no": transaction_id,
            # "cheque_date": formatted_date,
            "bill_date":formatted_date,
            "user_remark": f"Advance from {customer_name}",
            "custom_advance_type": custom_advance_type,
            "custom_patient_type": custom_patient_type,
            "custom_payer_type": payer_type,
            "custom_patient_name": patient_name,
            "custom_uhid": custom_uhid,
            "custom_bill_category": "UHID Advance",
            "accounts": accounts
            # "accounts": [
            #     {
            #         "account": paid_to_account,
            #         "debit_in_account_currency": amount,
            #         "account_currency": paid_to_account_currency
            #     },
            #     {
            #         "account": customer_advance_account,
            #         "credit_in_account_currency": amount,
            #         "account_currency": paid_to_account_currency,
            #         "party_type": "Customer",
            #         "party": customer,
            #         "is_advance":"Yes"
            #     }
            # ]
        })
        if transaction_id:
            journal_entry.cheque_no = transaction_id
            journal_entry.cheque_date = formatted_date
        else:
            journal_entry.cheque_no = None
            journal_entry.cheque_date = None
        journal_entry.insert()
        frappe.db.commit()
        journal_entry.submit()

        return f"Journal Entry {journal_entry.name} created successfully!"
    
    except Exception as e:
        frappe.log_error(f"Error creating Journal Entry: {str(e)}")
        print("Error creating Journal Entry")
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
        elif payer_type == "tpa":
            customer_group = "TPA"
        elif payer_type == "cash":
            customer_group = "Cash"
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

