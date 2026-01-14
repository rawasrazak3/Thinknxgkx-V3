
# import frappe
# import requests
# from frappe.utils import nowdate, getdate, add_days, cint
# from datetime import datetime, timedelta, time, timezone
# from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# billing_type = "AR BILL SETTLEMENT"
# settings = frappe.get_single("Karexpert Settings")
# TOKEN_URL = settings.get("token_url")
# BILLING_URL = settings.get("billing_url")
# facility_id = settings.get("facility_id")

# # Fetch row details based on billing type
# billing_row = frappe.get_value(
#     "Karexpert  Table",
#     {"billing_type": billing_type},
#     ["client_code", "integration_key", "x_api_key"],
#     as_dict=True
# )

# headers_token = fetch_api_details(billing_type)


# def get_or_create_customer(customer_name):
#     """Fetch existing customer or create a new one."""
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


# def get_jwt_token():
#     """Fetch JWT token from API."""
#     response = requests.post(TOKEN_URL, headers=headers_token)
#     if response.status_code == 200:
#         return response.json().get("jwttoken")
#     else:
#         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")


# def fetch_advance_billing(jwt_token, from_date, to_date):
#     """Fetch AR bill settlement data from API."""
#     headers_billing = {
#         "Content-Type": "application/json",
#         "clientCode": "ALNILE_THINKNXG_FI",
#         "integrationKey": "AR_BILL_SETTLEMENT",
#         "Authorization": f"Bearer {jwt_token}"
#     }
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch AR settlement data: {response.status_code} - {response.text}")


# @frappe.whitelist()
# def main():
#     try:
#         jwt_token = get_jwt_token()
#         frappe.logger().info("JWT Token fetched successfully.")

#         # Calculate from_date and to_date
#         to_date_raw = settings.get("date")
#         t_date = getdate(to_date_raw) if to_date_raw else add_days(nowdate(), -4)
#         no_of_days = cint(settings.get("no_of_days") or 25)
#         f_date = add_days(t_date, -no_of_days)

#         gmt_plus_4 = timezone(timedelta(hours=4))
#         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
#         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

#         billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
#         frappe.logger().info("AR settlement data fetched successfully.")

#           # GROUP BY BILL NO
#         bill_map = {}

#         for row in billing_data.get("jsonResponse", []):
#             ar = row.get("ar_transaction_detail", {})
#             bill_no = ar.get("bill_no")

#             if not bill_no:
#                 continue

#             bill_map.setdefault(bill_no, []).append(row)

#         #  CREATE ONE JE PER BILL
#         for bill_no, transactions in bill_map.items():
#             create_merged_journal_entry(bill_no, transactions)

#     except Exception as e:
#         frappe.log_error(f"AR Settlement Error: {e}")

#     #     for billing in billing_data.get("jsonResponse", []):
#     #         create_journal_entry(billing)

#     # except Exception as e:
#     #     frappe.log_error(f"Error: {e}")


# @frappe.whitelist()
# # def create_journal_entry(billing_data):
# #     """Create Journal Entry from AR settlement data."""
# #     try:
# #         frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")

# #         ar_details = billing_data.get("ar_transaction_detail", {})

# #         # Extract billing info
# #         bill_no = ar_details.get("bill_no")
# #         bill_amount = ar_details.get("bill_amount")
# #         admission_id = ar_details.get("admissionId")
# #         receipt_no = ar_details.get("receipt_no")
# #         uhid = ar_details.get("uhId")
# #         payment_details = ar_details.get("payment_detail", [])
# #         payer_details = ar_details.get("payer_authorization", [])
# #         write_off_amount = ar_details.get("write_off") or 0
# #         processing_fee_amount = ar_details.get("processing_fee") or 0
# #         tds_amount = ar_details.get("tds") or 0
# #         payer_deduct_amount = ar_details.get("payer_deduct_amount") or 0

# #         customer_name = ar_details.get("payer_name") or billing_data.get("customer")
# #         customer = get_or_create_customer(customer_name)

# #         patient_name = ar_details.get("patient_name")
# #         patient_type = ar_details.get("patientType")
# #         payer_type = ar_details.get("payer_type")
# #         mode_of_payment = ar_details.get("payment_mode")

# #         # Company accounts
# #         company = frappe.defaults.get_user_default("Company")
# #         company_doc = frappe.get_doc("Company", company)
# #         debit_account = company_doc.default_receivable_account
# #         credit_account = company_doc.default_income_account
# #         cash_account = company_doc.default_cash_account
# #         bank_account = company_doc.default_bank_account
# #         write_off_account = company_doc.write_off_account

# #         # Total amounts
# #         total_amount = sum(p.get("received_amount", 0) for p in payment_details)
# #         auth_amount = sum(p.get("authorization_amount", 0) for p in payer_details)
# #         if total_amount <= 0:
# #             return f"Failed: No valid payment amount for bill no {bill_no}"

# #         # Convert timestamp
# #         date_ms = ar_details.get("g_creation_time")
# #         dt = datetime.fromtimestamp(date_ms / 1000, timezone(timedelta(hours=4)))
# #         formatted_date = dt.strftime('%Y-%m-%d')

# #         # Check for duplicate JE
# #         existing_je = frappe.db.exists(
# #             "Journal Entry",
# #             {
# #                 "posting_date": formatted_date,
# #                 "docstatus": 1,
# #                 "user_remark": f"AR Settlement for Bill No: {bill_no}"
# #             }
# #         )
# #         if existing_je:
# #             frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation: {existing_je}")
# #             return f"Skipped: Journal Entry {existing_je} already exists"
        

# #         original_billing_je = frappe.get_all(
# #             "Journal Entry",
# #             filters={
# #                 "custom_bill_number": bill_no,
# #                 "custom_bill_category": "OP Billing",
# #                 "docstatus": 1
# #             },
# #             fields=["name"],
# #             limit=1
# #         )
# #         reference_invoice = original_billing_je[0]["name"] if original_billing_je else None

# #         if not reference_invoice:
# #             frappe.log(f"No original OP Billing JE found with bill No: {bill_no}")



# #         # Initialize JE entries
# #         je_entries = []

# #         # Credit the payer (customer)
# #         if bill_amount > 0:
# #             je_entries.append({
# #                 "account": debit_account,
# #                 "party_type": "Customer",
# #                 "party": customer,
# #                 "credit_in_account_currency": bill_amount,
# #                 "debit_in_account_currency": 0,
# #                 "reference_type": "Journal Entry",
# #                 "reference_name": reference_invoice,
# #             })

# #          # Write-off
# #         if write_off_amount > 0:
# #             je_entries.append({
# #                 "account": write_off_account,
# #                 "debit_in_account_currency": write_off_amount,
# #                 "credit_in_account_currency": 0
# #             })

# #         # processing amount
# #         if processing_fee_amount > 0:
# #             je_entries.append({
# #                 "account": "Processing Fee - AN",
# #                 "debit_in_account_currency": processing_fee_amount,
# #                 "credit_in_account_currency": 0
# #             })

# #         # tds amount
# #         if tds_amount > 0:
# #             je_entries.append({
# #                 "account": "TDS - AN",
# #                 "debit_in_account_currency": tds_amount,
# #                 "credit_in_account_currency": 0
# #             })

# #         # Payer Deduct Amount
# #         if payer_deduct_amount > 0:
# #             je_entries.append({
# #                 "account": "Payer Deduction - AN",
# #                 "debit_in_account_currency": payer_deduct_amount,
# #                 "credit_in_account_currency": 0
# #             })


# #         # Additional amounts
# #         # for name, value in [("Processing Fee", processing_fee_amount),
# #         #                     ("TDS", tds_amount),
# #         #                     ("Payer Deduct", payer_deduct_amount)]:
# #         #     if value > 0:
# #         #         je_entries.append({
# #         #             "account": debit_account,
# #         #             "debit_in_account_currency": value,
# #         #             "credit_in_account_currency": 0,
# #         #             "party_type": "Customer",
# #         #             "party": customer
# #         #         })

# #         # Debit each payment mode
# #         for payment in payment_details:
# #             mode = payment.get("payment_mode_code", "").lower()
# #             amount = payment.get("received_amount", 0)
# #             due_amount = payment.get("remaining_due_amount") or 0
# #             proc_fee = payment.get("processing_fee") or 0
# #             tds = payment.get("tds") or 0
# #             payer_deduct = payment.get("payer_deduct_amount") or 0

# #             if mode == "cash":
# #                 account = cash_account
# #             elif mode in ["upi", "card", "bank", "neft"]:
# #                 account = bank_account
# #             elif mode == "credit":
# #                 account = debit_account
# #             else:
# #                 account = bank_account

# #             # Debit received amount
# #             if amount > 0:
# #                 je_entries.append({
# #                     "account": account,
# #                     "debit_in_account_currency": amount,
# #                     "credit_in_account_currency": 0
# #                 })

# #         # Create Journal Entry
# #         je_doc = frappe.get_doc({
# #             "doctype": "Journal Entry",
# #             "posting_date": formatted_date,
# #             "accounts": je_entries,
# #             "user_remark": f"AR Settlement for Bill No: {bill_no}",
# #             "custom_bill_category": "AR BILL SETTLEMENT",
# #             "custom_bill_number": bill_no,
# #             "custom_uhid": uhid,
# #             "custom_payer_name": customer,
# #             "custom_receipt_no": receipt_no,
# #             "custom_admission_id": admission_id,
# #             "custom_patient_name": patient_name,
# #             "custom_patient_type": patient_type,
# #             "custom_payer_type": payer_type,
# #             "mode_of_payment": mode_of_payment,
# #         })
# #         je_doc.insert(ignore_permissions=True)
# #         frappe.db.commit()
# #         je_doc.submit()
# #         frappe.logger().info(f"[JE DEBUG] Journal Entry {je_doc.name} created successfully.")
# #         return je_doc.name

# #     except Exception as e:
# #         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
# #         frappe.logger().error(f"[JE DEBUG] Exception: {str(e)}")
# #         return f"Failed to create Journal Entry: {str(e)}"

# def create_merged_journal_entry(bill_no, transactions):
#     """
#     Create ONE consolidated JE per bill_no
#     """
#     try:
#         first = transactions[0]["ar_transaction_detail"]

#         customer = get_or_create_customer(first.get("payer_name"))
#         company = frappe.defaults.get_user_default("Company")
#         company_doc = frappe.get_doc("Company", company)

#         debit_account = company_doc.default_receivable_account
#         cash_account = company_doc.default_cash_account
#         bank_account = company_doc.default_bank_account
#         write_off_account = company_doc.write_off_account

#         total_bill_amount = first.get("bill_amount", 0)

#         #  MERGED TOTALS
#         total_write_off = 0
#         total_processing_fee = 0
#         total_tds = 0
#         total_payer_deduct = 0

#         original_billing_je = frappe.get_all(
#             "Journal Entry",
#             filters={
#                 "custom_bill_number": bill_no,
#                 "custom_bill_category": "OP Billing",
#                 "docstatus": 1
#             },
#             fields=["name"],
#             limit=1
#         )

#         reference_je = original_billing_je[0]["name"] if original_billing_je else None

#         if not reference_je:
#             frappe.log_error(
#                 f"OP Billing JE not found for Bill No {bill_no}",
#                 "AR Settlement Reference Missing"
#             )

#         je_entries = []

#         #  CREDIT CUSTOMER ONCE
#         je_entries.append({
#             "account": debit_account,
#             "party_type": "Customer",
#             "party": customer,
#             "credit_in_account_currency": total_bill_amount,
#             "debit_in_account_currency": 0,
#             "reference_type": "Journal Entry",
#             "reference_name": reference_je
#         })

#         #  PROCESS EACH TRANSACTION
#         for txn in transactions:
#             ar = txn["ar_transaction_detail"]

#             total_write_off += ar.get("write_off") or 0
#             total_processing_fee += ar.get("processing_fee") or 0
#             total_tds += ar.get("tds") or 0
#             total_payer_deduct += ar.get("payer_deduct_amount") or 0

#             for pay in ar.get("payment_detail", []):
#                 amount = pay.get("received_amount", 0)
#                 mode = pay.get("payment_mode_code", "").lower()

#                 if amount <= 0:
#                     continue

#                 account = (
#                     cash_account if mode == "cash"
#                     else bank_account
#                 )

#                 je_entries.append({
#                     "account": account,
#                     "debit_in_account_currency": amount,
#                     "credit_in_account_currency": 0
#                 })

#         # ADJUSTMENTS
#         if total_write_off > 0:
#             je_entries.append({
#                 "account": write_off_account,
#                 "debit_in_account_currency": total_write_off,
#                 "credit_in_account_currency": 0
#             })

#         if total_processing_fee > 0:
#             je_entries.append({
#                 "account": "Processing Fee - AN",
#                 "debit_in_account_currency": total_processing_fee,
#                 "credit_in_account_currency": 0
#             })

#         if total_tds > 0:
#             je_entries.append({
#                 "account": "TDS - AN",
#                 "debit_in_account_currency": total_tds,
#                 "credit_in_account_currency": 0
#             })

#         if total_payer_deduct > 0:
#             je_entries.append({
#                 "account": "Payer Deduction - AN",
#                 "debit_in_account_currency": total_payer_deduct,
#                 "credit_in_account_currency": 0
#             })

#         # CREATE JE
#         je = frappe.get_doc({
#             "doctype": "Journal Entry",
#             "posting_date": nowdate(),
#             "accounts": je_entries,
#             "user_remark": f"AR Settlement Consolidated for Bill No: {bill_no}",
#             "custom_bill_category": "AR BILL SETTLEMENT",
#             "custom_bill_number": bill_no
#         })

#         je.insert(ignore_permissions=True)
#         je.submit()

#         frappe.logger().info(f"Consolidated JE created for Bill {bill_no}: {je.name}")

#     except Exception as e:
#         frappe.log_error(f"Merge JE Error ({bill_no}): {e}")


import frappe
import requests
from frappe.utils import nowdate, getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "AR BILL SETTLEMENT"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value(
    "Karexpert  Table",
    {"billing_type": billing_type},
    ["client_code", "integration_key", "x_api_key"],
    as_dict=True
)

headers_token = fetch_api_details(billing_type)


def get_or_create_customer(customer_name, payer_type=None):
    # Determine customer group based on payer_type
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "insurance":
            customer_group = "Insurance"
        elif payer_type == "corporate":
            customer_group = "Corporate"
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


def get_jwt_token():
    """Fetch JWT token from API."""
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")


def fetch_advance_billing(jwt_token, from_date, to_date):
    """Fetch AR bill settlement data from API."""
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
        frappe.throw(f"Failed to fetch AR settlement data: {response.status_code} - {response.text}")


@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.logger().info("JWT Token fetched successfully.")

        # Calculate from_date and to_date
        to_date_raw = settings.get("date")
        t_date = getdate(to_date_raw) if to_date_raw else add_days(nowdate(), -4)
        no_of_days = cint(settings.get("no_of_days") or 25)
        f_date = add_days(t_date, -no_of_days)

        gmt_plus_4 = timezone(timedelta(hours=4))
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

        billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
        frappe.logger().info("AR settlement data fetched successfully.")

          # GROUP BY BILL NO
        bill_map = {}

        for row in billing_data.get("jsonResponse", []):
            ar = row.get("ar_transaction_detail", {})
            bill_no = ar.get("bill_no")

            if not bill_no:
                continue

            bill_map.setdefault(bill_no, []).append(row)

        #  CREATE ONE JE PER BILL
        for bill_no, transactions in bill_map.items():
            create_merged_journal_entry(bill_no, transactions)

    except Exception as e:
        frappe.log_error(f"AR Settlement Error: {e}")

    #     for billing in billing_data.get("jsonResponse", []):
    #         create_journal_entry(billing)

    # except Exception as e:
    #     frappe.log_error(f"Error: {e}")


@frappe.whitelist()
# def create_journal_entry(billing_data):
#     """Create Journal Entry from AR settlement data."""
#     try:
#         frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")

#         ar_details = billing_data.get("ar_transaction_detail", {})

#         # Extract billing info
#         bill_no = ar_details.get("bill_no")
#         bill_amount = ar_details.get("bill_amount")
#         admission_id = ar_details.get("admissionId")
#         receipt_no = ar_details.get("receipt_no")
#         uhid = ar_details.get("uhId")
#         payment_details = ar_details.get("payment_detail", [])
#         payer_details = ar_details.get("payer_authorization", [])
#         write_off_amount = ar_details.get("write_off") or 0
#         processing_fee_amount = ar_details.get("processing_fee") or 0
#         tds_amount = ar_details.get("tds") or 0
#         payer_deduct_amount = ar_details.get("payer_deduct_amount") or 0

#         customer_name = ar_details.get("payer_name") or billing_data.get("customer")
#         customer = get_or_create_customer(customer_name)

#         patient_name = ar_details.get("patient_name")
#         patient_type = ar_details.get("patientType")
#         payer_type = ar_details.get("payer_type")
#         mode_of_payment = ar_details.get("payment_mode")

#         # Company accounts
#         company = frappe.defaults.get_user_default("Company")
#         company_doc = frappe.get_doc("Company", company)
#         debit_account = company_doc.default_receivable_account
#         credit_account = company_doc.default_income_account
#         cash_account = company_doc.default_cash_account
#         bank_account = company_doc.default_bank_account
#         write_off_account = company_doc.write_off_account

#         # Total amounts
#         total_amount = sum(p.get("received_amount", 0) for p in payment_details)
#         auth_amount = sum(p.get("authorization_amount", 0) for p in payer_details)
#         if total_amount <= 0:
#             return f"Failed: No valid payment amount for bill no {bill_no}"

#         # Convert timestamp
#         date_ms = ar_details.get("g_creation_time")
#         dt = datetime.fromtimestamp(date_ms / 1000, timezone(timedelta(hours=4)))
#         formatted_date = dt.strftime('%Y-%m-%d')

#         # Check for duplicate JE
#         existing_je = frappe.db.exists(
#             "Journal Entry",
#             {
#                 "posting_date": formatted_date,
#                 "docstatus": 1,
#                 "user_remark": f"AR Settlement for Bill No: {bill_no}"
#             }
#         )
#         if existing_je:
#             frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation: {existing_je}")
#             return f"Skipped: Journal Entry {existing_je} already exists"
        

#         original_billing_je = frappe.get_all(
#             "Journal Entry",
#             filters={
#                 "custom_bill_number": bill_no,
#                 "custom_bill_category": "OP Billing",
#                 "docstatus": 1
#             },
#             fields=["name"],
#             limit=1
#         )
#         reference_invoice = original_billing_je[0]["name"] if original_billing_je else None

#         if not reference_invoice:
#             frappe.log(f"No original OP Billing JE found with bill No: {bill_no}")



#         # Initialize JE entries
#         je_entries = []

#         # Credit the payer (customer)
#         if bill_amount > 0:
#             je_entries.append({
#                 "account": debit_account,
#                 "party_type": "Customer",
#                 "party": customer,
#                 "credit_in_account_currency": bill_amount,
#                 "debit_in_account_currency": 0,
#                 "reference_type": "Journal Entry",
#                 "reference_name": reference_invoice,
#             })

#          # Write-off
#         if write_off_amount > 0:
#             je_entries.append({
#                 "account": write_off_account,
#                 "debit_in_account_currency": write_off_amount,
#                 "credit_in_account_currency": 0
#             })

#         # processing amount
#         if processing_fee_amount > 0:
#             je_entries.append({
#                 "account": "Processing Fee - AN",
#                 "debit_in_account_currency": processing_fee_amount,
#                 "credit_in_account_currency": 0
#             })

#         # tds amount
#         if tds_amount > 0:
#             je_entries.append({
#                 "account": "TDS - AN",
#                 "debit_in_account_currency": tds_amount,
#                 "credit_in_account_currency": 0
#             })

#         # Payer Deduct Amount
#         if payer_deduct_amount > 0:
#             je_entries.append({
#                 "account": "Payer Deduction - AN",
#                 "debit_in_account_currency": payer_deduct_amount,
#                 "credit_in_account_currency": 0
#             })


#         # Additional amounts
#         # for name, value in [("Processing Fee", processing_fee_amount),
#         #                     ("TDS", tds_amount),
#         #                     ("Payer Deduct", payer_deduct_amount)]:
#         #     if value > 0:
#         #         je_entries.append({
#         #             "account": debit_account,
#         #             "debit_in_account_currency": value,
#         #             "credit_in_account_currency": 0,
#         #             "party_type": "Customer",
#         #             "party": customer
#         #         })

#         # Debit each payment mode
#         for payment in payment_details:
#             mode = payment.get("payment_mode_code", "").lower()
#             amount = payment.get("received_amount", 0)
#             due_amount = payment.get("remaining_due_amount") or 0
#             proc_fee = payment.get("processing_fee") or 0
#             tds = payment.get("tds") or 0
#             payer_deduct = payment.get("payer_deduct_amount") or 0

#             if mode == "cash":
#                 account = cash_account
#             elif mode in ["upi", "card", "bank", "neft"]:
#                 account = bank_account
#             elif mode == "credit":
#                 account = debit_account
#             else:
#                 account = bank_account

#             # Debit received amount
#             if amount > 0:
#                 je_entries.append({
#                     "account": account,
#                     "debit_in_account_currency": amount,
#                     "credit_in_account_currency": 0
#                 })

#         # Create Journal Entry
#         je_doc = frappe.get_doc({
#             "doctype": "Journal Entry",
#             "posting_date": formatted_date,
#             "accounts": je_entries,
#             "user_remark": f"AR Settlement for Bill No: {bill_no}",
#             "custom_bill_category": "AR BILL SETTLEMENT",
#             "custom_bill_number": bill_no,
#             "custom_uhid": uhid,
#             "custom_payer_name": customer,
#             "custom_receipt_no": receipt_no,
#             "custom_admission_id": admission_id,
#             "custom_patient_name": patient_name,
#             "custom_patient_type": patient_type,
#             "custom_payer_type": payer_type,
#             "mode_of_payment": mode_of_payment,
#         })
#         je_doc.insert(ignore_permissions=True)
#         frappe.db.commit()
#         je_doc.submit()
#         frappe.logger().info(f"[JE DEBUG] Journal Entry {je_doc.name} created successfully.")
#         return je_doc.name

#     except Exception as e:
#         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
#         frappe.logger().error(f"[JE DEBUG] Exception: {str(e)}")
#         return f"Failed to create Journal Entry: {str(e)}"

def create_merged_journal_entry(bill_no, transactions):
    """
    Create ONE consolidated JE per bill_no
    """
    try:
        first = transactions[0]["ar_transaction_detail"]

        customer = get_or_create_customer(first.get("payer_name"))
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)

        debit_account = company_doc.default_receivable_account
        cash_account = company_doc.default_cash_account
        bank_account = company_doc.default_bank_account
        write_off_account = company_doc.write_off_account

        total_bill_amount = first.get("bill_amount", 0)

        #  MERGED TOTALS
        total_write_off = 0
        total_processing_fee = 0
        total_tds = 0
        total_payer_deduct = 0

        original_billing_je = frappe.get_all(
            "Journal Entry",
            filters={
                "custom_bill_number": bill_no,
                "custom_bill_category": "OP Billing",
                "docstatus": 1
            },
            fields=["name"],
            limit=1
        )

        reference_je = original_billing_je[0]["name"] if original_billing_je else None

        if not reference_je:
            frappe.log_error(
                f"OP Billing JE not found for Bill No {bill_no}",
                "AR Settlement Reference Missing"
            )

        je_entries = []

        #  CREDIT CUSTOMER ONCE
        je_entries.append({
            "account": debit_account,
            "party_type": "Customer",
            "party": customer,
            "credit_in_account_currency": total_bill_amount,
            "debit_in_account_currency": 0,
            "reference_type": "Journal Entry",
            "reference_name": reference_je
        })

        #  PROCESS EACH TRANSACTION
        for txn in transactions:
            ar = txn["ar_transaction_detail"]

            total_write_off += ar.get("write_off") or 0
            total_processing_fee += ar.get("processing_fee") or 0
            total_tds += ar.get("tds") or 0
            total_payer_deduct += ar.get("payer_deduct_amount") or 0

            for pay in ar.get("payment_detail", []):
                amount = pay.get("received_amount", 0)
                mode = pay.get("payment_mode_code", "").lower()

                if amount <= 0:
                    continue

                account = (
                    cash_account if mode == "cash"
                    else bank_account
                )

                je_entries.append({
                    "account": account,
                    "debit_in_account_currency": amount,
                    "credit_in_account_currency": 0
                })

        # ADJUSTMENTS
        if total_write_off > 0:
            je_entries.append({
                "account": write_off_account,
                "debit_in_account_currency": total_write_off,
                "credit_in_account_currency": 0
            })

        if total_processing_fee > 0:
            je_entries.append({
                "account": "Processing Fee - AN",
                "debit_in_account_currency": total_processing_fee,
                "credit_in_account_currency": 0
            })

        if total_tds > 0:
            je_entries.append({
                "account": "TDS - AN",
                "debit_in_account_currency": total_tds,
                "credit_in_account_currency": 0
            })

        if total_payer_deduct > 0:
            je_entries.append({
                "account": "Payer Deduction - AN",
                "debit_in_account_currency": total_payer_deduct,
                "credit_in_account_currency": 0
            })

        # CREATE JE
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": nowdate(),
            "accounts": je_entries,
            "user_remark": f"AR Settlement Consolidated for Bill No: {bill_no}",
            "custom_bill_category": "AR BILL SETTLEMENT",
            "custom_bill_number": bill_no
        })

        je.insert(ignore_permissions=True)
        je.submit()

        frappe.logger().info(f"Consolidated JE created for Bill {bill_no}: {je.name}")

    except Exception as e:
        frappe.log_error(f"Merge JE Error ({bill_no}): {e}")