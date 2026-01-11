# # # import frappe
# # # import requests
# # # import json
# # # from frappe.utils import nowdate
# # # from frappe.utils import getdate
# # # from datetime import datetime


# # # TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# # # BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"

# # # headers_token = {
# # #     "Content-Type": "application/json",
# # #     "clientCode": "METRO_THINKNXG_FI",
# # #     "facilityId": "METRO_THINKNXG",
# # #     "messageType": "request",
# # #     "integrationKey": "ADVANCE_DEPOSIT_REFUND",
# # #     "x-api-key": "yrwetnb987zxauyt765"
# # # }

# # import frappe
# # import requests
# # import json
# # from frappe.utils import nowdate
# # from datetime import datetime
# # from datetime import datetime, timedelta,  timezone, time
# # from frappe.utils import getdate, add_days, cint
# # from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# # billing_type = "ADVANCE DEPOSIT REFUND"
# # settings = frappe.get_single("Karexpert Settings")
# # TOKEN_URL = settings.get("token_url")
# # BILLING_URL = settings.get("billing_url")
# # facility_id = settings.get("facility_id")

# # # Fetch row details based on billing type
# # billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
# #                                 ["client_code", "integration_key", "x_api_key"], as_dict=True)

# # headers_token = fetch_api_details(billing_type)


# # def get_jwt_token():
# #     response = requests.post(TOKEN_URL, headers=headers_token)
# #     if response.status_code == 200:
# #         return response.json().get("jwttoken")
# #     else:
# #         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

# # def fetch_advance_billing(jwt_token, from_date, to_date):
# #     headers_billing = {
# #         "Content-Type": "application/json",
# #         "clientCode": "ALNILE_THINKNXG_FI",
# #         "integrationKey": "ADVANCE_DEPOSIT_REFUND",
# #         "Authorization": f"Bearer {jwt_token}"
# #     }
# #     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
# #     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
# #     if response.status_code == 200:
# #         return response.json()
# #     else:
# #         frappe.throw(f"Failed to fetch Advance Deposut Refund data: {response.status_code} - {response.text}")


# # @frappe.whitelist()
# # def main():
# #     try:
# #         jwt_token = get_jwt_token()
# #         frappe.log("JWT Token fetched successfully.")

# #         # from_date = 1752148536000  
# #         # to_date =  1754654136000    
# #         # Fetch dynamic date and number of days from settings
# #         settings = frappe.get_single("Karexpert Settings")
# #         # Get to_date from settings or fallback to nowdate() - 4 days
# #         to_date_raw = settings.get("date")
# #         if to_date_raw:
# #             to_date = getdate(to_date_raw)
# #         else:
# #             to_date = add_days(nowdate(), -4)

# #         # Get no_of_days from settings and calculate from_date
# #         no_of_days = cint(settings.get("no_of_days") or 3)  # default 3 days if not set
# #         from_date = add_days(to_date, -no_of_days)
# #         # Define GMT+4 timezone
# #         gmt_plus_4 = timezone(timedelta(hours=4))

# #         # Convert to timestamps in milliseconds for GMT+4
# #         from_date = int(datetime.combine(from_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
# #         print("from", from_date)
# #         to_date = int(datetime.combine(to_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
# #         billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
# #         frappe.log("Advance Refund Billing data fetched successfully.")

# #         for billing in billing_data.get("jsonResponse", []):
# #             create_advance_refund_entry(billing["advance_refund"])

# #     except Exception as e:
# #         frappe.log_error(f"Error: {e}")

# # if __name__ == "__main__":
# #     main()

# # def create_advance_refund_entry(billing_data):
# #     try:
# #         mode_of_payment = billing_data["payment_transaction_details"][0]["payment_mode_display"]

# #         mode_of_payment_accounts = frappe.get_all(
# #             "Mode of Payment Account",
# #             filters={"parent": mode_of_payment},
# #             fields=["default_account"],
# #             limit=1
# #         )

# #         if not mode_of_payment_accounts:
# #             return f"Failed: No default account found for mode of payment {mode_of_payment}"
# #         # --- Fetch accounts dynamically from Company ---
# #         company = frappe.defaults.get_user_default("Company")
# #         company_doc = frappe.get_doc("Company", company)
# #         cash_account = company_doc.default_cash_account
# #         bank_account = company_doc.default_bank_account
# #         card_account = company_doc.default_bank_account

# #         # Use fixed account based on mode of payment
# #         if mode_of_payment.lower() == "Cash":
# #             paid_to_account = cash_account
# #         elif mode_of_payment.lower() == "Bank Transfer":
# #             paid_to_account = bank_account
# #         else:                                  # Card Payment
# #             paid_to_account = card_account

# #         paid_to_account_currency = frappe.db.get_value("Account", paid_to_account, "account_currency")

# #         transaction_date_time = billing_data["payment_transaction_details"][0].get("transaction_date_time")
# #         if not transaction_date_time:
# #             return "Failed: Transaction Date is missing."

# #         # Define GMT+4 offset
# #         gmt_plus_4 = timezone(timedelta(hours=4))
# #         dt = datetime.fromtimestamp(transaction_date_time / 1000.0, gmt_plus_4)
# #         print("formt", dt)
# #         formatted_date = dt.strftime('%Y-%m-%d')
# #         print("date--", formatted_date)

# #         reference_no = billing_data.get("receipt_no")
# #         if not reference_no:
# #             return "Failed: Reference No is missing."

# #         existing_je = frappe.get_value(
# #             "Journal Entry",
# #             {
# #                 "bill_no": reference_no
# #             },
# #             "name"
# #         )

# #         if frappe.db.exists("Journal Entry", {"custom_bill_number": reference_no}):
# #             return f"Skipped: Journal Entry already exists."


    
# #         transaction_id = ""
# #         for tx in billing_data.get("payment_transaction_details", []):
# #             if tx.get("transaction_id"):
# #                 transaction_id = tx.get("transaction_id")
# #                 break

# #         frappe.log_error("Transaction ID: " + str(transaction_id), "Advance Billing Log")


# #         # Check for existing Journal Entry
# #         existing_je = frappe.get_value(
# #             "Journal Entry",
# #             {"cheque_no": reference_no, "posting_date": formatted_date},
# #             "name"
# #         )
# #         if existing_je:
# #             return f"Skipped: Journal Entry {existing_je} already exists."

# #         customer_name = billing_data.get("patient_name")
# #         customer = get_or_create_customer(customer_name)

# #         custom_advance_type = billing_data.get("advance_type")
# #         custom_patient_type = billing_data.get("patient_type_display")
# #         custom_uh_id = billing_data.get("uhId")
# #         amount = billing_data.get("amount")

# #         # Fetch default receivable account or use a custom "Customer Advances" account
# #         # customer_advance_account = frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_receivable_account")
# #         customer_advance_account = "Advance Received - AN"
# #         journal_entry = frappe.get_doc({
# #             "doctype": "Journal Entry",
# #             "posting_date": formatted_date,
# #             "voucher_type" : "Credit Note",
# #             "custom_bill_number": reference_no,
# #             "bill_date":formatted_date,
# #             "remark": f"Advance refund to {customer_name}",
# #             "custom_advance_type": custom_advance_type,
# #             "custom_patient_type": custom_patient_type,
# #             "custom_uhid": custom_uh_id,
# #             "custom_bill_category": "UHID Advance Refund",
# #             "accounts": [
# #                 {
# #                     "account": paid_to_account,
# #                     "credit_in_account_currency": amount,
# #                     "account_currency": paid_to_account_currency
# #                 },
# #                 {
# #                     "account": customer_advance_account,
# #                     "debit_in_account_currency": amount,
# #                     "account_currency": paid_to_account_currency,
# #                     "party_type": "Customer",
# #                     "party": customer,
# #                     "is_advance":"Yes"
# #                 }
# #             ]
# #         })
# #         if transaction_id:
# #             journal_entry.cheque_no = transaction_id
# #             journal_entry.cheque_date = formatted_date
# #         journal_entry.insert()
# #         frappe.db.commit()
# #         journal_entry.submit()

# #         return f"Journal Entry {journal_entry.name} created successfully!"
    
# #     except Exception as e:
# #         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
# #         return f"Failed to create Journal Entry: {str(e)}"


# # def get_or_create_customer(customer_name):
# #     existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name})
# #     if existing_customer:
# #         return existing_customer
    
# #     customer = frappe.get_doc({
# #         "doctype": "Customer",
# #         "customer_name": customer_name,
# #         "customer_group": "Individual",
# #         "territory": "All Territories"
# #     })
# #     customer.insert(ignore_permissions=True)
# #     frappe.db.commit()
# #     return customer.name

# import frappe
# import requests
# import json
# from frappe.utils import nowdate, getdate, add_days, cint
# from datetime import datetime, timedelta, timezone, time
# from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# billing_type = "ADVANCE DEPOSIT REFUND"
# settings = frappe.get_single("Karexpert Settings")
# TOKEN_URL = settings.get("token_url")
# BILLING_URL = settings.get("billing_url")


# # Fetch row details based on billing type
# headers_token = fetch_api_details(billing_type)


# def get_jwt_token():
#     response = requests.post(TOKEN_URL, headers=headers_token)
#     if response.status_code == 200:
#         return response.json().get("jwttoken")
#     else:
#         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")


# def fetch_advance_billing(jwt_token, from_date, to_date):
#     headers_billing = {
#         "Content-Type": "application/json",
#         "clientCode": "ALNILE_THINKNXG_FI",
#         "integrationKey": "ADVANCE_DEPOSIT_REFUND",
#         "Authorization": f"Bearer {jwt_token}"
#     }
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch Advance Deposit Refund data: {response.status_code} - {response.text}")


# @frappe.whitelist()
# def main():
#     try:
#         jwt_token = get_jwt_token()
#         frappe.log("JWT Token fetched successfully.")

#         # Get dynamic dates from settings
#         to_date_raw = settings.get("date")
#         if to_date_raw:
#             to_date = getdate(to_date_raw)
#         else:
#             to_date = add_days(nowdate(), -4)

#         no_of_days = cint(settings.get("no_of_days") or 3)
#         from_date = add_days(to_date, -no_of_days)

#         # Convert to timestamps in milliseconds (GMT+4)
#         gmt_plus_4 = timezone(timedelta(hours=4))
#         from_timestamp = int(datetime.combine(from_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
#         to_timestamp = int(datetime.combine(to_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

#         billing_data = fetch_advance_billing(jwt_token, from_timestamp, to_timestamp)
#         frappe.log("Advance Refund Billing data fetched successfully.")

#         for billing in billing_data.get("jsonResponse", []):
#             advance_refund = billing.get("advance_refund")
#             if advance_refund:
#                 create_advance_refund_entry(advance_refund)

#     except Exception as e:
#         frappe.log_error(f"Error: {e}")


# def create_advance_refund_entry(billing_data):
#     try:
#         payment_details = billing_data.get("payment_transaction_details")
#         if not payment_details:
#             return "Failed: No payment transaction details available."

#         mode_of_payment = payment_details[0].get("payment_mode_display", "Cash").title()
#         transaction_id = payment_details[0].get("transaction_id") or ""
#         transaction_date_time = payment_details[0].get("transaction_date_time")
#         if not transaction_date_time:
#             return "Failed: Transaction Date is missing."

#         # GMT+4 timezone
#         gmt_plus_4 = timezone(timedelta(hours=4))
#         dt = datetime.fromtimestamp(transaction_date_time / 1000.0, gmt_plus_4)
#         formatted_date = dt.strftime('%Y-%m-%d')

#         reference_no = billing_data.get("receipt_no")
#         if not reference_no:
#             return "Failed: Reference No is missing."

#         # Skip if Journal Entry already exists
#         if frappe.db.exists("Journal Entry", {"custom_bill_number": reference_no}):
#             return f"Skipped: Journal Entry {reference_no} already exists."

#         # Fetch default accounts
#         company = frappe.defaults.get_user_default("Company")
#         company_doc = frappe.get_doc("Company", company)
#         cash_account = company_doc.default_cash_account
#         bank_account = company_doc.default_bank_account
#         card_account = company_doc.default_bank_account

#         if mode_of_payment.lower() == "cash":
#             paid_to_account = cash_account
#         elif mode_of_payment.lower() in ["bank transfer", "bank"]:
#             paid_to_account = bank_account
#         else:
#             paid_to_account = card_account

#         paid_to_account_currency = frappe.db.get_value("Account", paid_to_account, "account_currency")

#         # Customer
#         customer_name = billing_data.get("patient_name") or "Unknown"
#         customer = get_or_create_customer(customer_name)

#         # Amount
#         amount = billing_data.get("amount") or 0.0

#         # Journal Entry
#         customer_advance_account = "Advance Received - AN"
#         journal_entry = frappe.get_doc({
#             "doctype": "Journal Entry",
#             "posting_date": formatted_date,
#             "voucher_type": "Credit Note",
#             "custom_bill_number": reference_no,
#             "bill_date": formatted_date,
#             "remark": f"Advance refund to {customer_name}",
#             "custom_advance_type": billing_data.get("advance_type") or "",
#             "custom_patient_type": billing_data.get("patient_type_display") or "",
#             "custom_uhid": billing_data.get("uhId") or "",
#             "custom_bill_category": "UHID Advance Refund",
#             "accounts": [
#                 {
#                     "account": paid_to_account,
#                     "credit_in_account_currency": amount,
#                     "account_currency": paid_to_account_currency
#                 },
#                 {
#                     "account": customer_advance_account,
#                     "debit_in_account_currency": amount,
#                     "account_currency": paid_to_account_currency,
#                     "party_type": "Customer",
#                     "party": customer,
#                     "is_advance": "Yes"
#                 }
#             ]
#         })

#         if transaction_id:
#             journal_entry.cheque_no = transaction_id
#             journal_entry.cheque_date = formatted_date

#         journal_entry.insert()
#         frappe.db.commit()
#         journal_entry.submit()

#         return f"Journal Entry {journal_entry.name} created successfully!"

#     except Exception as e:
#         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
#         return f"Failed to create Journal Entry: {str(e)}"


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


# import frappe
# import requests
# import json
# from frappe.utils import nowdate
# from frappe.utils import getdate
# from datetime import datetime


# TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"

# headers_token = {
#     "Content-Type": "application/json",
#     "clientCode": "METRO_THINKNXG_FI",
#     "facilityId": "METRO_THINKNXG",
#     "messageType": "request",
#     "integrationKey": "ADVANCE_DEPOSIT_REFUND",
#     "x-api-key": "yrwetnb987zxauyt765"
# }

import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from datetime import datetime, timedelta,  timezone, time
from frappe.utils import getdate, add_days, cint
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "ADVANCE DEPOSIT REFUND"
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
        "integrationKey": "ADVANCE_DEPOSIT_REFUND",
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch Advance Deposut Refund data: {response.status_code} - {response.text}")


@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # from_date = 1752148536000  
        # to_date =  1754654136000    
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
        print("from", from_date)
        to_date = int(datetime.combine(to_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
        billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
        frappe.log("Advance Refund Billing data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_advance_refund_entry(billing["advance_refund"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

def create_advance_refund_entry(billing_data):
    try:
        mode_of_payment = billing_data["payment_transaction_details"][0]["payment_mode_display"]

        mode_of_payment_accounts = frappe.get_all(
            "Mode of Payment Account",
            filters={"parent": mode_of_payment},
            fields=["default_account"],
            limit=1
        )

        if not mode_of_payment_accounts:
            return f"Failed: No default account found for mode of payment {mode_of_payment}"
        # --- Fetch accounts dynamically from Company ---
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)
        cash_account = company_doc.default_cash_account
        bank_account = company_doc.default_bank_account
        card_account = company_doc.default_bank_account

        # Use fixed account based on mode of payment
        if mode_of_payment.lower() == "Cash":
            paid_to_account = cash_account
        elif mode_of_payment.lower() == "Card Payment":
            paid_to_account = card_account
        else:                                  # Card Payment
            paid_to_account = bank_account

        paid_to_account_currency = frappe.db.get_value("Account", paid_to_account, "account_currency")

        transaction_date_time = billing_data["payment_transaction_details"][0].get("transaction_date_time")
        if not transaction_date_time:
            return "Failed: Transaction Date is missing."

        # Define GMT+4 offset
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(transaction_date_time / 1000.0, gmt_plus_4)
        print("formt", dt)
        formatted_date = dt.strftime('%Y-%m-%d')
        print("date--", formatted_date)

        reference_no = billing_data.get("receipt_no")
        if not reference_no:
            return "Failed: Reference No is missing."

        existing_je = frappe.get_value(
            "Journal Entry",
            {
                "custom_bill_number": reference_no
            },
            "name"
        )

        if frappe.db.exists("Journal Entry", {"custom_bill_number": reference_no}):
            return f"Skipped: Journal Entry already exists."


    
        transaction_id = ""
        for tx in billing_data.get("payment_transaction_details", []):
            if tx.get("transaction_id"):
                transaction_id = tx.get("transaction_id")
                break

        frappe.log_error("Transaction ID: " + str(transaction_id), "Advance Billing Log")


        # Check for existing Journal Entry
        existing_je = frappe.get_value(
            "Journal Entry",
            {"cheque_no": reference_no, "posting_date": formatted_date},
            "name"
        )
        if existing_je:
            return f"Skipped: Journal Entry {existing_je} already exists."

        customer_name = billing_data.get("patient_name")
        customer = get_or_create_customer(customer_name)

        custom_advance_type = billing_data.get("advance_type")
        custom_patient_type = billing_data.get("patient_type_display")
        custom_uh_id = billing_data.get("uhId")
        amount = billing_data.get("amount")

        # Fetch default receivable account or use a custom "Customer Advances" account
        # customer_advance_account = frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_receivable_account")
        customer_advance_account = "Advance Received - AN"
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "voucher_type" : "Credit Note",
            "custom_bill_number": reference_no,
            "bill_date":formatted_date,
            "remark": f"Advance refund to {customer_name}",
            "custom_advance_type": custom_advance_type,
            "custom_patient_type": custom_patient_type,
            "custom_uhid": custom_uh_id,
            "custom_bill_category": "UHID Advance Refund",
            "accounts": [
                {
                    "account": paid_to_account,
                    "credit_in_account_currency": amount,
                    "account_currency": paid_to_account_currency
                },
                {
                    "account": customer_advance_account,
                    "debit_in_account_currency": amount,
                    "account_currency": paid_to_account_currency,
                    "party_type": "Customer",
                    "party": customer,
                    "is_advance":"Yes"
                }
            ]
        })
        if transaction_id:
            journal_entry.cheque_no = transaction_id
            journal_entry.cheque_date = formatted_date
        journal_entry.insert()
        frappe.db.commit()
        journal_entry.submit()

        return f"Journal Entry {journal_entry.name} created successfully!"
    
    except Exception as e:
        frappe.log_error(f"Error creating Journal Entry: {str(e)}")
        return f"Failed to create Journal Entry: {str(e)}"


def get_or_create_customer(customer_name, payer_type=None):
    if payer_type and payer_type.lower() == "cash":
            return None
     # Check if the customer already exists
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":payer_type})
    if existing_customer:
        return existing_customer

    # Determine customer group based on payer_type
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "Insurance":
            customer_group = "Insurance"
        elif payer_type == "Cash":
            customer_group = "Cash"
        elif payer_type == "Corporate":
            customer_group = "Corporate"
        elif payer_type == "Credit":
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
