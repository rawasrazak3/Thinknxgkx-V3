import frappe
import requests
from frappe.utils import nowdate, getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "AR BILL SETTLEMENT"

settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")

headers_token = fetch_api_details(billing_type)


# -------------------- CUSTOMER --------------------
def get_or_create_customer(customer_name, payer_type=None):
    if payer_type and payer_type.lower() == "cash":
        return None

    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "insurance":
            customer_group = "Insurance"
        elif payer_type == "corporate":
            customer_group = "Corporate"
        elif payer_type == "tpa":
            customer_group = "TPA"
        elif payer_type == "credit":
            customer_group = "Credit"
        else:
            customer_group = "Cash"
    else:
        customer_group = "Cash"

    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name})
    if existing_customer:
        return existing_customer

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_group": customer_group,
        "territory": "All Territories"
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()

    return customer.name


# -------------------- TOKEN --------------------
def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Token Error: {response.status_code} - {response.text}")


# -------------------- FETCH DATA --------------------
def fetch_advance_billing(jwt_token, from_date, to_date):
    headers_billing = {
        "Content-Type": "application/json",
        "clientCode": "ALNILE_THINKNXG_FI",
        "integrationKey": "AR_BILL_SETTLEMENT",
        "Authorization": f"Bearer {jwt_token}"
    }

    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}

    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Billing Fetch Error: {response.status_code} - {response.text}")


# -------------------- MAIN --------------------
@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()

        # Date calculation
        to_date_raw = settings.get("date")
        t_date = getdate(to_date_raw) if to_date_raw else getdate(add_days(nowdate(), -2))
        no_of_days = cint(settings.get("no_of_days") or 3)
        f_date = getdate(add_days(t_date, -no_of_days))

        gmt_plus_4 = timezone(timedelta(hours=4))
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

        billing_data = fetch_advance_billing(jwt_token, from_date, to_date)

        # Group by transaction_id
        txn_map = {}

        for row in billing_data.get("jsonResponse", []):
            ar = row.get("ar_transaction_detail", {})

            payment_details = ar.get("payment_detail", [])
            if not payment_details:
                continue

            txn_id = payment_details[0].get("transaction_id")
            if not txn_id:
                continue

            txn_map.setdefault(txn_id, []).append(row)

        for txn_id, transactions in txn_map.items():
            create_merged_journal_entry(txn_id, transactions)

        frappe.msgprint("AR Bill created successfully")

    except Exception as e:
        frappe.log_error(f"Main Error: {e}")


# -------------------- CREATE MERGED JE --------------------
@frappe.whitelist()
def create_merged_journal_entry(txn_id, transactions):
    try:
        # Avoid duplicate
        if frappe.db.exists("Journal Entry", {"cheque_no": txn_id, "docstatus": ["!=", 2]}):
            return

        first = transactions[0]["ar_transaction_detail"]

        customer = get_or_create_customer(first.get("payer_name"))
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)

        receivable_account = company_doc.default_receivable_account

        settlement_date = first.get("settlement_date")
        posting_date = datetime.fromtimestamp(settlement_date / 1000).date() if settlement_date else nowdate()

        total_received_amount = 0
        total_authorized_amount = 0

        # -------------------- PROCESS --------------------
        for txn in transactions:
            ar = txn.get("ar_transaction_detail", {})

            # # SUM AUTHORIZATION
            # for auth in ar.get("payer_authorization", []):
            #     total_authorized_amount += auth.get("authorization_amount", 0)

            # SUM RECEIVED
            for pay in ar.get("payment_detail", []):
                total_received_amount += pay.get("received_amount", 0)

        je_entries = []
        
        # -------------------- CREDIT (AUTHORIZED SUM) --------------------
        if total_received_amount > 0:
            je_entries.append({
                "account": receivable_account,
                "party_type": "Customer",
                "party": customer,
                "credit_in_account_currency": total_received_amount,
                "project": "AR BILL SETTLEMENT",
                "bank_account": "0429028333140012 - BANK MUSCAT"
            })

        # -------------------- DEBIT (BANK SUM) --------------------
        if total_received_amount > 0:
            je_entries.append({
                "account": "0429028333140012 - BANK MUSCAT - AN",
                "debit_in_account_currency": total_received_amount,
                "project": "AR BILL SETTLEMENT"
            })

        if not je_entries:
            return

        # -------------------- CREATE JE --------------------
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "naming_series": "KX-JV-.YYYY.-",
            "posting_date": posting_date,
            "cheque_no": txn_id,
            "cheque_date": posting_date,
            "accounts": je_entries,
            "user_remark": f"AR Settlement Consolidated - Transaction ID: {txn_id}",
            "custom_bill_category": "AR BILL SETTLEMENT",
            "custom_transaction_id": txn_id,
        })

        je.insert(ignore_permissions=True)
        je.submit()

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Merge JE Error ({txn_id}): {e}")