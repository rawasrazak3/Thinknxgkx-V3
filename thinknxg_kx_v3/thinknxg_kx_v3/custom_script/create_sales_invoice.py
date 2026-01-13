# import frappe
# import requests
# import json
# from frappe.utils import nowdate
# from datetime import datetime
# from frappe.utils import getdate, add_days, cint
# from datetime import datetime, timedelta, time, timezone
# from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details
# billing_type = "OP BILLING"
# settings = frappe.get_single("Karexpert Settings")
# TOKEN_URL = settings.get("token_url")
# BILLING_URL = settings.get("billing_url")
# facility_id = settings.get("facility_id")

# # Fetch row details based on billing type
# billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
#                                 ["client_code", "integration_key", "x_api_key"], as_dict=True)


# headers_token = fetch_api_details(billing_type)
# # TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# # BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"
# # headers_token = {
# #     "Content-Type": "application/json",
# #     # "clientCode": "METRO_THINKNXG_FI",
# #     "clientCode": billing_row["client_code"],
# #     # "facilityId": "METRO_THINKNXG",
# #     "facilityId": facility_id,
# #     "messageType": "request",
# #     # "integrationKey": "OP_BILLING",
# #     "integrationKey": billing_row["integration_key"],
# #     # "x-api-key": "kfhgjfgjf0980gdfgfds"
# #     "x-api-key": billing_row["x_api_key"]
# # }

# def get_jwt_token():
#     response = requests.post(TOKEN_URL, headers=headers_token)
#     if response.status_code == 200:
#         return response.json().get("jwttoken")
#     else:
#         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

# def fetch_op_billing(jwt_token, from_date, to_date):
#     headers_billing = {
#         "Content-Type": headers_token["Content-Type"],
#         # "clientCode": "ALNILE_THINKNXG_FI",
#         "clientCode": headers_token["clientCode"],
#         # "integrationKey": "OP_BILLING",
#         "integrationKey": headers_token["integrationKey"],
#         "Authorization": f"Bearer {jwt_token}"
#     }
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch OP Billing data: {response.status_code} - {response.text}")

# def get_or_create_customer(customer_name, payer_type=None):
#     print("creating or getting customer")
#     # If payer type is cash, don't create a customer
#     if payer_type and payer_type.lower() == "cash":
#         return None
#     # Check if the customer already exists
#     existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":payer_type})
#     if existing_customer:
#         return existing_customer

#     # Determine customer group based on payer_type
#     if payer_type:
#         payer_type = payer_type.lower()
#         if payer_type == "insurance":
#             customer_group = "Insurance"
#         elif payer_type == "cash":
#             customer_group = "Cash"
#         elif payer_type == "corporate":
#             customer_group = "Corporate"
#         elif payer_type == "tpa":
#             customer_group = "TPA"
#         elif payer_type == "credit":
#             customer_group = "Credit"
#         else:
#             customer_group = "Individual"  # default fallback
#     else:
#         customer_group = "Individual"

#     # Create new customer
#     customer = frappe.get_doc({
#         "doctype": "Customer",
#         "customer_name": customer_name,
#         "customer_group": customer_group,
#         "territory": "All Territories"
#     })
#     customer.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return customer.name

# def get_or_create_patient(patient_name,gender,uhid):
#     existing_patient = frappe.db.exists("Patient", {"patient_name": patient_name})
#     if existing_patient:
#         return existing_patient
    
#     customer = frappe.get_doc({
#         "doctype": "Patient",
#         "first_name": patient_name,
#         "sex": gender,
#         "uid":uhid
#     })
#     customer.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return customer.name


# # def get_or_create_cost_center(department, sub_department):
# #     parent_cost_center_name = f"{department}(G)"
# #     sub_cost_center_name = f"{sub_department}"

# #     # Check if parent cost center exists, if not, create it
# #     existing_parent = frappe.db.exists("Cost Center", {"cost_center_name": parent_cost_center_name})
# #     if not existing_parent:
# #         parent_cost_center = frappe.get_doc({
# #             "doctype": "Cost Center",
# #             "cost_center_name": parent_cost_center_name,
# #             "parent_cost_center": "METRO HOSPITALS & POLYCLINCS LLC - MH",  # Root level
# #             "is_group":1,
# #             "company": frappe.defaults.get_defaults().get("company")
# #         })
# #         parent_cost_center.insert(ignore_permissions=True)
# #         frappe.db.commit()
# #         existing_parent = parent_cost_center.name

# #     # Check if sub cost center exists, if not, create it
# #     existing_sub = frappe.db.exists("Cost Center", {"cost_center_name": sub_cost_center_name})
# #     if existing_sub:
# #         return existing_sub

# #     sub_cost_center = frappe.get_doc({
# #         "doctype": "Cost Center",
# #         "cost_center_name": sub_cost_center_name,
# #         "parent_cost_center": existing_parent,
# #         "company": frappe.defaults.get_defaults().get("company")
# #     })
# #     sub_cost_center.insert(ignore_permissions=True)
# #     frappe.db.commit()

# #     return sub_cost_center.name

# def get_or_create_cost_center(treating_department_name):
#     cost_center_name = f"{treating_department_name} - AN"
    
#     # Check if the cost center already exists by full name
#     existing = frappe.db.exists("Cost Center", cost_center_name)
#     if existing:
#         return cost_center_name
    
#     # Determine parent based on treating_department_name
#     if treating_department_name is not None :
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
#         billing_data = fetch_op_billing(jwt_token, from_date, to_date)
#         frappe.log("OP Billing data fetched successfully.")

#         for billing in billing_data.get("jsonResponse", []):
#             create_journal_entry_from_billing(billing["op_billing"])

#     except Exception as e:
#         frappe.log_error(f"Error: {e}")

# if __name__ == "__main__":
#     main()

# def create_journal_entry_from_billing(billing_data):
#     bill_no = billing_data["bill_no"]
#     payment_details = billing_data.get("payment_transaction_details", [])
#     date = billing_data["g_creation_time"]
#     modification_time = billing_data.get("g_modify_time", date)  # fallback if not present
#     mod_date = modification_time / 1000.0

#     # Define GMT+4
#     gmt_plus_4 = timezone(timedelta(hours=4))
#     mod_dt = datetime.fromtimestamp(mod_date, gmt_plus_4)
#     mod_time = mod_dt.strftime('%Y-%m-%d %H:%M:%S')

#     # Check if JE already exists
#     existing_je = frappe.db.get_value(
#         "Journal Entry",
#         {"custom_bill_number": bill_no, "docstatus": 1},
#         ["name", "custom_modification_time"],
#         as_dict=True
#     )

#     if existing_je:
#         stored_mod_time = existing_je.get("custom_modification_time")
#         # If modification_time is same or earlier, skip
#         if stored_mod_time and str(stored_mod_time) == str(mod_time):
#             frappe.log(f"JE for bill {bill_no} already exists and is up-to-date. Skipping...")
#             return existing_je["name"]

#         # Else cancel and recreate
#         try:
#             je_doc = frappe.get_doc("Journal Entry", existing_je["name"])
#             je_doc.cancel()
#             frappe.db.commit()
#             frappe.log(f"Cancelled JE {existing_je['name']} for modified bill {bill_no}")
#         except Exception as e:
#             frappe.log_error(f"Failed to cancel JE {existing_je['name']}: {e}")
#             return None
#     datetimes = date / 1000.0

#     # Define GMT+4
#     gmt_plus_4 = timezone(timedelta(hours=4))
#     dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
#     formatted_date = dt.strftime('%Y-%m-%d')
#     posting_time = dt.strftime('%H:%M:%S')

    

#     if frappe.db.exists("Journal Entry", {"custom_bill_number": bill_no, "docstatus": ["!=", 2]}):
#         frappe.log(f"Journal Entry with bill_no {bill_no} already exists.")
#         return

#     # Patient & Customer
#     customer_name = billing_data["payer_name"]
#     payer_type = billing_data["payer_type"]
#     patient_name = billing_data["patient_name"]
#     gender = billing_data["patient_gender"]
#     uhid = billing_data["uhId"]
#     customer = get_or_create_customer(customer_name,payer_type)
#     patient = get_or_create_patient(patient_name, gender,uhid)

#     treating_department_name = billing_data.get("treating_department_name", "Default Dept")
#     cost_center = get_or_create_cost_center(treating_department_name)
#     # Amounts
#     is_due = billing_data["is_due"]
#     due_amount= billing_data["due_amount"]

#     if is_due== "true":
#             item_rate = billing_data["total_amount"]-due_amount
#     else:
#             item_rate = billing_data["total_amount"]



#     authorized_amount = billing_data.get("authorized_amount", 0)
#     payer_amounts = billing_data.get("received_amount", 0)
#     payer_amount = authorized_amount + payer_amounts

#     discount_amount = billing_data["selling_amount"] - billing_data["total_amount"]
#     tax_amount = billing_data["tax"]

#     # --- Fetch accounts dynamically from Company ---
#     company = frappe.defaults.get_user_default("Company")
#     company_doc = frappe.get_doc("Company", company)

#     debit_account = company_doc.default_receivable_account
#     credit_account = company_doc.default_income_account
#     cash_account = company_doc.default_cash_account
#     bank_account = company_doc.default_bank_account
   

#     # vat_account = getattr(company_doc, "default_tax_account", None) or frappe.db.get_single_value("Company", "default_tax_account")
#     vat_account = "Output VAT 5% - AN"
#     default_expense_account = company_doc.default_expense_account
#     default_stock_in_hand = company_doc.default_inventory_account
#     if payer_type.lower() == "cash":
#         customer_advance_account = "Advance Received - AN"
#     else:
#         customer_advance_account = "Debtors - AN"
#     # discount_account = getattr(company_doc, "default_discount_account", None) or frappe.db.get_single_value("Company", "default_discount_account")

#     if not debit_account or not credit_account:
#         frappe.throw("Please set Default Receivable and Income accounts in Company settings.")

#     total_uepr = sum(
#         (item.get("ueprValue") or 0)
#         for item in billing_data.get("item_details", [])
#     )

#     je_accounts = [
#         # {
#         #     "account": debit_account,
#         #     "party_type": "Customer",
#         #     "party": customer,
#         #     "debit_in_account_currency": item_rate + tax_amount,
#         #     "credit_in_account_currency": 0,
#         #     "cost_center": cost_center
#         # },
#         {
#             "account": credit_account,
#             "debit_in_account_currency": 0,
#             "credit_in_account_currency": item_rate,
#             "cost_center": cost_center
#         },
#     ]
#     # Handling Credit Payment Mode
#     # credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "prepaid card"), None)

#     # Find the prepaid card payment
#     credit_payment = next(
#         (p for p in payment_details if p.get("payment_mode_code", "").lower() == "prepaid card"),
#         None
#     )

#     if credit_payment:
#         debit_amount = credit_payment.get("amount", 0)
#         if debit_amount > 0:
#             je_accounts.append({
#                 "account": debit_account,  # e.g., Receivable or specific customer account
#                 "party_type": "Customer",
#                 "party": customer,
#                 "debit_in_account_currency": debit_amount,
#                 "credit_in_account_currency": 0,
#             })

#     # Handling Authorized Amount
#     if authorized_amount>0:
#         je_accounts.append({
#             "account": debit_account,  # Replace with actual debtors account
#             "party_type": "Customer",
#             "party": customer,
#             "debit_in_account_currency": authorized_amount,
#             "credit_in_account_currency": 0,
#         })
        

#     # Handling Cash Payment Mode
#     for payment in payment_details:
#         if payment["payment_mode_code"].lower() == "cash":
#             je_accounts.append({
#                 "account": cash_account,  # Replace with actual cash account
#                 "debit_in_account_currency": payment["amount"],    # Cash received
#                 "credit_in_account_currency": 0
#             })

#     # Handling Advance Payment Mode
#     for payment in payment_details:
#         if payment["payment_mode_code"].lower() in ["ip advance","uhid_advance"]:
#             je_accounts.append({
#                 "account": customer_advance_account,  # Replace with actual advance account
#                 "debit_in_account_currency": payment["amount"],
#                 "credit_in_account_currency": 0
#             })

#     # Handling Other Payment Modes (UPI, Card, etc.)
#     bank_payment_total = sum(
#         p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "prepaid card","IP ADVANCE","uhid_advance"]
#     )
#     if bank_payment_total > 0:
#         je_accounts.append({
#             "account": bank_account,  # Replace with actual bank account
#             "debit_in_account_currency": bank_payment_total,
#             "credit_in_account_currency": 0,
#             # "reference_type": "Sales Invoice",
#             # "reference_name":sales_invoice_name
#         })

#     # Handling due amount
#     # if is_due == "true" and due_amount > 0:
#     #     je_accounts.append({
#     #         "account": "Due Ledger - AN",  # Replace with actual bank account
#     #         "debit_in_account_currency": due_amount,
#     #         "credit_in_account_currency": 0,
#     #     #     "reference_type": "Sales Invoice",
#     #     #     "reference_name":sales_invoice_name
#     #     })

#     if billing_data.get("is_due") and due_amount > 0:
#         je_accounts.append({
#             "account": "Due Ledger - AN",
#             "debit_in_account_currency": due_amount,  
#             "credit_in_account_currency": 0,
#             "party_type": "Customer",
#             "party": customer,
#             "cost_center": cost_center
#     })


#     # Tax line
#     if tax_amount > 0:
#         if not vat_account:
#             frappe.throw("Please set Default Tax Account in Company settings.")
#         je_accounts.append({
#             "account": vat_account,
#             "debit_in_account_currency": 0,
#             "credit_in_account_currency": tax_amount,
#             "cost_center": cost_center
#         })
#     if total_uepr > 0:
#         je_accounts.extend([
#             {
#                 "account": default_expense_account,
#                 "debit_in_account_currency": total_uepr,
#                 "credit_in_account_currency": 0,
#                 "cost_center": cost_center
#             },
#             {
#                 "account": default_stock_in_hand,
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": total_uepr,
#                 "cost_center": cost_center
#             }
#         ])


#     # # Discount line
#     # if discount_amount > 0:
#     #     if not discount_account:
#     #         frappe.throw("Please set Default Discount Account in Company settings.")
#     #     je_accounts.append({
#     #         "account": discount_account,
#     #         "debit_in_account_currency": discount_amount,
#     #         "credit_in_account_currency": 0,
#     #         "cost_center": cost_center
#     #     })

#     # --- Create Journal Entry ---
#     je = frappe.get_doc({
#         "doctype": "Journal Entry",
#         "naming_series": "KX-JV-.YYYY.-",
#         "voucher_type": "Journal Entry",
#         "posting_date": formatted_date,
#         "posting_time": posting_time,
#         "custom_modification_time": mod_time,  # store mod time
#         "custom_patient_name": patient_name,
#         "custom_patient": patient_name,
#         "custom_bill_number": bill_no,
#         "custom_bill_category" :"OP Billing",
#         "custom_payer_name": customer_name,
#         "custom_uhid": billing_data["uhId"],
#         "custom_discount_amount": discount_amount,
#         "custom_admission_id": billing_data["admissionId"],
#         "custom_admission_type": billing_data["admissionType"],
#         "company": company,
#         "user_remark": f"OP Billing for bill no {bill_no}" ,
#         "accounts": je_accounts
#     })

#     try:
#         je.insert(ignore_permissions=True)
#         je.submit()
#         frappe.db.commit()
#         frappe.log(f"Journal Entry created successfully with bill_no: {bill_no}")
#         return je.name
#     except Exception as e:
#         frappe.log_error(f"Failed to create Journal Entry: {e}")
#         return None


import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details
billing_type = "OP BILLING"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)


headers_token = fetch_api_details(billing_type)
# TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"
# headers_token = {
#     "Content-Type": "application/json",
#     # "clientCode": "METRO_THINKNXG_FI",
#     "clientCode": billing_row["client_code"],
#     # "facilityId": "METRO_THINKNXG",
#     "facilityId": facility_id,
#     "messageType": "request",
#     # "integrationKey": "OP_BILLING",
#     "integrationKey": billing_row["integration_key"],
#     # "x-api-key": "kfhgjfgjf0980gdfgfds"
#     "x-api-key": billing_row["x_api_key"]
# }

def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

# def fetch_op_billing(jwt_token, from_date, to_date):
#     headers_billing = {
#         "Content-Type": headers_token["Content-Type"],
#         # "clientCode": "ALNILE_THINKNXG_FI",
#         "clientCode": headers_token["clientCode"],
#         # "integrationKey": "OP_BILLING",
#         "integrationKey": headers_token["integrationKey"],
#         "Authorization": f"Bearer {jwt_token}"
#     }
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch OP Billing data: {response.status_code} - {response.text}")

def fetch_op_billing(jwt_token, from_date, to_date):
    print("fetching op billing...")
    headers_billing = {
        "Content-Type": headers_token["Content-Type"],
        "clientCode": headers_token["clientCode"],
        "integrationKey": headers_token["integrationKey"],
        "Authorization": f"Bearer {jwt_token}"
    }
    print("headers:", headers_billing)
    

    # Convert milliseconds timestamps to ISO date strings
    from_date_str = datetime.fromtimestamp(from_date / 1000, tz=timezone(timedelta(hours=4))).strftime("%Y-%m-%d")
    to_date_str   = datetime.fromtimestamp(to_date / 1000, tz=timezone(timedelta(hours=4))).strftime("%Y-%m-%d")
    print("from date")
    print(from_date_str)
    print("to date")
    print(to_date_str)

    payload = {"requestJson": {"FROM": from_date_str, "TO": to_date_str}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    # print(response.json())
    # print("response above")

    if response.status_code == 200:
        if response.text.strip() == "":
            frappe.log(f"API returned empty response for dates {from_date_str} - {to_date_str}")
            print("empty response")
            return {"jsonResponse": []}
        try:
            return response.json()
        except json.JSONDecodeError:
            frappe.log(f"Invalid JSON returned: {response.text}")
            return {"jsonResponse": []}
    else:
        frappe.throw(f"Failed to fetch OP Billing data: {response.status_code} - {response.text}")


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

def get_or_create_patient(patient_name,gender,uhid):
    existing_patient = frappe.db.exists("Patient", {"patient_name": patient_name})
    if existing_patient:
        return existing_patient
    
    customer = frappe.get_doc({
        "doctype": "Patient",
        "first_name": patient_name,
        "sex": gender,
        "uid":uhid
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()
    return customer.name


# def get_or_create_cost_center(department, sub_department):
#     parent_cost_center_name = f"{department}(G)"
#     sub_cost_center_name = f"{sub_department}"

#     # Check if parent cost center exists, if not, create it
#     existing_parent = frappe.db.exists("Cost Center", {"cost_center_name": parent_cost_center_name})
#     if not existing_parent:
#         parent_cost_center = frappe.get_doc({
#             "doctype": "Cost Center",
#             "cost_center_name": parent_cost_center_name,
#             "parent_cost_center": "METRO HOSPITALS & POLYCLINCS LLC - MH",  # Root level
#             "is_group":1,
#             "company": frappe.defaults.get_defaults().get("company")
#         })
#         parent_cost_center.insert(ignore_permissions=True)
#         frappe.db.commit()
#         existing_parent = parent_cost_center.name

#     # Check if sub cost center exists, if not, create it
#     existing_sub = frappe.db.exists("Cost Center", {"cost_center_name": sub_cost_center_name})
#     if existing_sub:
#         return existing_sub

#     sub_cost_center = frappe.get_doc({
#         "doctype": "Cost Center",
#         "cost_center_name": sub_cost_center_name,
#         "parent_cost_center": existing_parent,
#         "company": frappe.defaults.get_defaults().get("company")
#     })
#     sub_cost_center.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return sub_cost_center.name

def get_or_create_cost_center(treating_department_name):
    cost_center_name = f"{treating_department_name} - AN"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Cost Center", cost_center_name)
    if existing:
        return cost_center_name
    
    # Determine parent based on treating_department_name
    if treating_department_name is not None :
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
        # print("---f", from_date)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
        # print("----t", to_date)
        billing_data = fetch_op_billing(jwt_token, from_date, to_date)
        frappe.log("OP Billing data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry_from_billing(billing["op_billing"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

def create_journal_entry_from_billing(billing_data):
    print("billing details")
    print(billing_data)
    bill_no = billing_data["bill_no"]
    payment_details = billing_data.get("payment_transaction_details", [])
    date = billing_data["g_creation_time"]
    modification_time = billing_data.get("g_modify_time", date)  # fallback if not present
    mod_date = modification_time / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    mod_dt = datetime.fromtimestamp(mod_date, gmt_plus_4)
    mod_time = mod_dt.strftime('%Y-%m-%d %H:%M:%S')

    # Check if JE already exists
    existing_je = frappe.db.get_value(
        "Journal Entry",
        {"custom_bill_number": bill_no, "docstatus": 1},
        ["name", "custom_modification_time"],
        as_dict=True
    )

    if existing_je:
        stored_mod_time = existing_je.get("custom_modification_time")
        # If modification_time is same or earlier, skip
        if stored_mod_time and str(stored_mod_time) == str(mod_time):
            frappe.log(f"JE for bill {bill_no} already exists and is up-to-date. Skipping...")
            return existing_je["name"]

        # Else cancel and recreate
        try:
            je_doc = frappe.get_doc("Journal Entry", existing_je["name"])
            je_doc.cancel()
            frappe.db.commit()
            frappe.log(f"Cancelled JE {existing_je['name']} for modified bill {bill_no}")
        except Exception as e:
            frappe.log_error(f"Failed to cancel JE {existing_je['name']}: {e}")
            return None
    datetimes = date / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    formatted_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')

    

    if frappe.db.exists("Journal Entry", {"custom_bill_number": bill_no, "docstatus": ["!=", 2]}):
        frappe.log(f"Journal Entry with bill_no {bill_no} already exists.")
        return

    # Patient & Customer
    customer_name = billing_data["payer_name"]
    payer_type = billing_data["payer_type"]
    patient_name = billing_data["patient_name"]
    gender = billing_data["patient_gender"]
    uhid = billing_data["uhId"]
    customer = get_or_create_customer(customer_name,payer_type)
    patient = get_or_create_patient(patient_name, gender,uhid)

    treating_department_name = billing_data.get("treating_department_name")
    cost_center = get_or_create_cost_center(treating_department_name)
    # Amounts
    is_due = billing_data["is_due"]
    due_amount= billing_data["due_amount"]

    if is_due== "true":
            item_rate = billing_data["total_amount"]-due_amount
    else:
            item_rate = billing_data["total_amount"]



    authorized_amount = billing_data.get("authorized_amount", 0)
    payer_amounts = billing_data.get("received_amount", 0)
    payer_amount = authorized_amount + payer_amounts

    discount_amount = billing_data["selling_amount"] - billing_data["total_amount"]
    tax_amount = billing_data["tax"]

    # --- Fetch accounts dynamically from Company ---
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company)

    debit_account = company_doc.default_receivable_account
    credit_account = company_doc.default_income_account
    cash_account = company_doc.default_cash_account
    bank_account = company_doc.default_bank_account
   

    # vat_account = getattr(company_doc, "default_tax_account", None) or frappe.db.get_single_value("Company", "default_tax_account")
    vat_account = "VAT 5% - AN"
    default_expense_account = company_doc.default_expense_account
    default_stock_in_hand = company_doc.default_inventory_account
    if payer_type.lower() == "cash":
        customer_advance_account = "Advance Received - AN"
    else:
        customer_advance_account = "Debtors - AN"
    # discount_account = getattr(company_doc, "default_discount_account", None) or frappe.db.get_single_value("Company", "default_discount_account")

    if not debit_account or not credit_account:
        frappe.throw("Please set Default Receivable and Income accounts in Company settings.")

    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in billing_data.get("item_details", [])
    )

    je_accounts = [
        # {
        #     "account": debit_account,
        #     "party_type": "Customer",
        #     "party": customer,
        #     "debit_in_account_currency": item_rate + tax_amount,
        #     "credit_in_account_currency": 0,
        #     "cost_center": cost_center
        # },
        {
            "account": credit_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": item_rate,
            "cost_center": cost_center
        },
    ]
    # Handling Credit Payment Mode
    credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
    if authorized_amount>0:
        je_accounts.append({
            "account": debit_account,  # Replace with actual debtors account
            "party_type": "Customer",
            "party": customer,
            "debit_in_account_currency": authorized_amount,
            "credit_in_account_currency": 0,
        })
        

    # Handling Cash Payment Mode
    for payment in payment_details:
        if payment["payment_mode_code"].lower() == "cash":
            je_accounts.append({
                "account": cash_account,  # Replace with actual cash account
                "debit_in_account_currency": payment["amount"],    # Cash received
                "credit_in_account_currency": 0
            })

    # Handling Advance Payment Mode
    for payment in payment_details:
        if payment["payment_mode_code"].lower() in ["ip advance","uhid_advance"]:
            je_accounts.append({
                "account": customer_advance_account,  # Replace with actual advance account
                "debit_in_account_currency": payment["amount"],
                "credit_in_account_currency": 0
            })

    # Handling Other Payment Modes (UPI, Card, etc.)
    bank_payment_total = sum(
        p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "credit","IP ADVANCE","uhid_advance"]
    )
    if bank_payment_total > 0:
        je_accounts.append({
            "account": bank_account,  # Replace with actual bank account
            "debit_in_account_currency": bank_payment_total,
            "credit_in_account_currency": 0,
            # "reference_type": "Sales Invoice",
            # "reference_name":sales_invoice_name
        })

    # Handling due amount
    # if is_due == "true" and due_amount > 0:
    #     je_accounts.append({
    #         "account": "Due Ledger - AN",  # Replace with actual bank account
    #         "debit_in_account_currency": due_amount,
    #         "credit_in_account_currency": 0,
    #     #     "reference_type": "Sales Invoice",
    #     #     "reference_name":sales_invoice_name
    #     })

    if billing_data.get("is_due") and due_amount > 0:
        je_accounts.append({
            "account": "Due Ledger - AN",
            "debit_in_account_currency": due_amount,  
            "credit_in_account_currency": 0,
            "party_type": "Customer",
            "party": customer,
            "cost_center": cost_center
    })


    # Tax line
    if tax_amount > 0:
        if not vat_account:
            frappe.throw("Please set Default Tax Account in Company settings.")
        je_accounts.append({
            "account": vat_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": tax_amount,
            "cost_center": cost_center
        })
    if total_uepr > 0:
        je_accounts.extend([
            {
                "account": default_expense_account,
                "debit_in_account_currency": total_uepr,
                "credit_in_account_currency": 0,
                "cost_center": cost_center
            },
            {
                "account": default_stock_in_hand,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": total_uepr,
                "cost_center": cost_center
            }
        ])


    # # Discount line
    # if discount_amount > 0:
    #     if not discount_account:
    #         frappe.throw("Please set Default Discount Account in Company settings.")
    #     je_accounts.append({
    #         "account": discount_account,
    #         "debit_in_account_currency": discount_amount,
    #         "credit_in_account_currency": 0,
    #         "cost_center": cost_center
    #     })

    # --- Create Journal Entry ---
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "naming_series": "KX-JV-.YYYY.-",
        "voucher_type": "Journal Entry",
        "posting_date": formatted_date,
        "posting_time": posting_time,
        "custom_modification_time": mod_time,  # store mod time
        "custom_patient_name": patient_name,
        "custom_patient": patient_name,
        "custom_bill_number": bill_no,
        "custom_bill_category" :"OP Billing",
        "custom_payer_name": customer_name,
        "custom_uhid": billing_data["uhId"],
        "custom_discount_amount": discount_amount,
        "custom_admission_id": billing_data["admissionId"],
        "custom_admission_type": billing_data["admissionType"],
        "company": company,
        "user_remark": f"OP Billing for bill no {bill_no}" ,
        "accounts": je_accounts
    })

    try:
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.db.commit()
        frappe.log(f"Journal Entry created successfully with bill_no: {bill_no}")
        return je.name
    except Exception as e:
        frappe.log_error(f"Failed to create Journal Entry: {e}")
        return None