# # # import frappe
# # # import requests
# # # import json
# # # from frappe.utils import nowdate
# # # from datetime import datetime
# # # from frappe.utils import getdate, add_days, cint
# # # from datetime import datetime, timedelta,time,timezone
# # # from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# # # billing_type = "DUE SETTLEMENT"
# # # settings = frappe.get_single("Karexpert Settings")
# # # TOKEN_URL = settings.get("token_url")
# # # BILLING_URL = settings.get("billing_url")
# # # facility_id = settings.get("facility_id")

# # # # Fetch row details based on billing type
# # # billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
# # #                                 ["client_code", "integration_key", "x_api_key"], as_dict=True)

# # # headers_token = fetch_api_details(billing_type)


# # # def get_jwt_token():
# # #     response = requests.post(TOKEN_URL, headers=headers_token)
# # #     if response.status_code == 200:
# # #         return response.json().get("jwttoken")
# # #     else:
# # #         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

# # # def fetch_advance_billing(jwt_token, from_date, to_date):
# # #     headers_billing = {
# # #         "Content-Type": "application/json",
# # #         "clientCode": "ALNILE_THINKNXG_FI",
# # #         "integrationKey": "BILLING_DUE_SETTLEMENT",
# # #         "Authorization": f"Bearer {jwt_token}"
# # #     }
# # #     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
# # #     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
# # #     if response.status_code == 200:
# # #         return response.json()
# # #     else:
# # #         frappe.throw(f"Failed to due settlement data: {response.status_code} - {response.text}")
# # # @frappe.whitelist()
# # # def main():
# # #     try:
# # #         jwt_token = get_jwt_token()
# # #         frappe.log("JWT Token fetched successfully.")

# # #         # from_date = 1672531200000  
# # #         # to_date = 1966962420000    
# # #         # Fetch dynamic date and number of days from settings
# # #         settings = frappe.get_single("Karexpert Settings")
# # #         # Get to_date from settings or fallback to nowdate() - 4 days
# # #         to_date_raw = settings.get("date")
# # #         if to_date_raw:
# # #             t_date = getdate(to_date_raw)
# # #         else:
# # #             t_date = add_days(nowdate(), -4)

# # #         # Get no_of_days from settings and calculate from_date
# # #         no_of_days = cint(settings.get("no_of_days") or 25)  # default 3 days if not set
# # #         f_date = add_days(t_date, -no_of_days)
# # #          # Define GMT+4 timezone
# # #         gmt_plus_4 = timezone(timedelta(hours=4))

# # #         # Convert to timestamps in milliseconds for GMT+4
# # #         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
# # #         print("---f", from_date)
# # #         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
# # #         print("----t", to_date)

# # #         billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
# # #         frappe.log("Due settlement data fetched successfully.")

# # #         for billing in billing_data.get("jsonResponse", []):
# # #             create_journal_entry(billing["due_settlement"])

# # #     except Exception as e:
# # #         frappe.log_error(f"Error: {e}")

# # # if __name__ == "__main__":
# # #     main()

# # # def create_journal_entry(billing_data):
# # #     try:
# # #         bill_no = billing_data["bill_no"]

# # #         payment_details = billing_data.get("payment_transaction_details", [])
        
# # #         # --- Fetch accounts dynamically from Company ---
# # #         company = frappe.defaults.get_user_default("Company")
# # #         company_doc = frappe.get_doc("Company", company)

# # #         debit_account = company_doc.default_receivable_account
# # #         credit_account = company_doc.default_income_account
# # #         cash_account = company_doc.default_cash_account
# # #         bank_account = company_doc.default_bank_account
# # #         write_off_account = company_doc.write_off_account

# # #         authorized_amount = billing_data.get("authorized_amount", 0)
# # #         payer_amounts = billing_data.get("received_amount", 0)
# # #         payer_amount = authorized_amount + payer_amounts

# # #         # Initialize journal entry rows
# # #         je_entries = []
# # #         je_entries.append({
# # #                 "account": "Due Ledger - AN",
# # #                 "debit_in_account_currency": 0,
# # #                 "credit_in_account_currency": payer_amount,
# # #             })
# # #         # Handling Credit Payment Mode
# # #         credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
# # #         if authorized_amount>0:
# # #             je_entries.append({
# # #                 "account": "Debtors - AN",  # Replace with actual debtors account
# # #                 "debit_in_account_currency": authorized_amount,
# # #                 "credit_in_account_currency": 0,
# # #             })
            

# # #         # Handling Cash Payment Mode
# # #         for payment in payment_details:
# # #             if payment["payment_mode_code"].lower() == "cash":
# # #                 je_entries.append({
# # #                     "account": cash_account,  # Replace with actual cash account
# # #                     "debit_in_account_currency": payment["amount"],
# # #                     "credit_in_account_currency": 0
# # #                 })

# # #         # Handling Other Payment Modes (UPI, Card, etc.)
# # #         bank_payment_total = sum(
# # #             p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "credit","IP ADVANCE"]
# # #         )
# # #         if bank_payment_total > 0:
# # #             je_entries.append({
# # #                 "account": bank_account,  # Replace with actual bank account
# # #                 "debit_in_account_currency": bank_payment_total,
# # #                 "credit_in_account_currency": 0
# # #             })

# # #         # Create Journal Entry if there are valid transactions
# # #         if je_entries:
# # #             je_doc = frappe.get_doc({
# # #                 "doctype": "Journal Entry",
# # #                 "posting_date": nowdate(),
# # #                 "accounts": je_entries,
# # #                 "user_remark": f"Due Settlement of: {bill_no}"
# # #             })
# # #             je_doc.insert(ignore_permissions=True)
# # #             frappe.db.commit()

# # #             # Link Journal Entry to Sales Invoice
# # #             # frappe.db.set_value("Sales Invoice", sales_invoice_name, "journal_entry", je_doc.name)
# # #             frappe.msgprint(f"Journal Entry {je_doc.name} created successfully.")
    
# # #     except Exception as e:
# # #         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
# # #         return f"Failed to create Journal Entry: {str(e)}"



# # import frappe
# # import requests
# # import json
# # from frappe.utils import nowdate
# # from datetime import datetime
# # from frappe.utils import getdate, add_days, cint
# # from datetime import datetime, timedelta, time, timezone
# # from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# # billing_type = "DUE SETTLEMENT"
# # settings = frappe.get_single("Karexpert Settings")
# # TOKEN_URL = settings.get("token_url")
# # BILLING_URL = settings.get("billing_url")

# # # Fetch row details based on billing type
# # billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
# #                                 ["client_code", "integration_key", "x_api_key"], as_dict=True)

# # headers_token = fetch_api_details(billing_type)


# # def fetch_advance_billing(jwt_token, from_date, to_date, headers):
# #     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
# #     headers_billing = headers.copy()
# #     headers_billing["Authorization"] = f"Bearer {jwt_token}"

# #     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
# #     if response.status_code == 200:
# #         return response.json()
# #     else:
# #         frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")


# # @frappe.whitelist()
# # def main():
# #     try:
# #         settings = frappe.get_single("Karexpert Settings")

# #         # Collect all facility IDs from child table
# #         facility_list = [row.facility_id for row in settings.get("facility_id_details") or [] if row.facility_id]

# #         if not facility_list:
# #             frappe.throw("No facility IDs found in Karexpert Settings.")

# #         # Prepare date range
# #         to_date_raw = settings.get("date")
# #         t_date = getdate(to_date_raw) if to_date_raw else getdate(add_days(nowdate(), 0))
# #         no_of_days = cint(settings.get("no_of_days") or 25)
# #         f_date = getdate(add_days(t_date, -no_of_days))

# #         # Convert to timestamps (GMT+4)
# #         gmt_plus_4 = timezone(timedelta(hours=4))
# #         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
# #         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

# #         all_billing_data = []

# #         # Loop through each facility
# #         for row in settings.get("facility_id_details") or []:
# #             facility_id = row.facility_id
# #             if not facility_id:
# #                 continue

# #             # Prepare headers for this facility
# #             billing_row = frappe.get_value(
# #                 "Karexpert  Table",
# #                 {"billing_type": "DUE SETTLEMENT"},
# #                 ["client_code", "integration_key", "x_api_key"],
# #                 as_dict=True
# #             )

# #             headers = {
# #                 "Content-Type": "application/json",
# #                 "clientCode": billing_row["client_code"],
# #                 "integrationKey": billing_row["integration_key"],
# #                 "facilityId": facility_id,
# #                 "messageType": "request",
# #                 "x-api-key": billing_row["x_api_key"]
# #             }

# #             # Fetch JWT for this facility
# #             jwt_token = get_jwt_token_for_headers(headers)

# #             frappe.log(f"Fetching AR bill settlement for Facility ID: {facility_id}")
# #             print("Fetching aAR bill settlement for Facility ID",facility_id)
# #             billing_data = fetch_advance_billing(jwt_token, from_date, to_date, headers)

# #             if billing_data and "jsonResponse" in billing_data:
# #                 all_billing_data.extend(billing_data["jsonResponse"])
# #             else:
# #                 frappe.log(f"No data returned for {facility_id}")

# #         # ✅ Process all collected billing data
# #         for billing in all_billing_data:
# #             create_journal_entry(billing['due_settlement'])

# #         frappe.log("All facility AR bill settlement data processed successfully.")

# #     except Exception as e:
# #         frappe.log_error(f"Error in AR bill settlement Fetch: {e}")


# # def get_jwt_token_for_headers(headers):
# #     """
# #     Fetch JWT token using the provided headers dict.
# #     """
# #     try:
# #         response = requests.post(TOKEN_URL, headers=headers, timeout=10)
# #         if response.status_code == 200:
# #             return response.json().get("jwttoken")
# #         else:
# #             frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")
# #     except requests.exceptions.RequestException as e:
# #         frappe.throw(f"JWT request failed: {e}")

# # if __name__ == "__main__":
# #     main()

# # @frappe.whitelist()
# # def create_journal_entry(billing_data):
# #     try:
# #         frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")
# #         # frappe.msgprint(f"[DEBUG] Received billing_data: {billing_data}")
        
# #         ar_details = billing_data
# #         bill_no = ar_details.get("bill_no")
# #         admission_id = ar_details.get("admissionId")
# #         receipt_no = ar_details.get("receipt_no")
# #         uhid = ar_details.get("uhId")
# #         payment_details = ar_details.get("payment_transaction_details", [])
# #         rec_amount = ar_details.get("received_amount")
# #         customer_name = ar_details.get("payer_name") or billing_data.get("customer")
# #         payer_type = ar_details.get("payer_type") or billing_data["payer_type"]
# #         customer = get_or_create_customer(customer_name,payer_type)
# #         # --- Fetch accounts dynamically from Company ---
# #         company = frappe.defaults.get_user_default("Company")
# #         company_doc = frappe.get_doc("Company", company)

# #         debit_account = company_doc.default_receivable_account
# #         credit_account = company_doc.default_income_account
# #         cash_account = company_doc.default_cash_account
# #         bank_account = company_doc.default_bank_account
# #         frappe.logger().info(f"[JE DEBUG] Bill No: {bill_no}")
# #         # frappe.msgprint(f"[DEBUG] Bill No: {bill_no}")
# #         frappe.logger().info(f"[JE DEBUG] Customer Name: {customer_name}")
# #         # frappe.msgprint(f"[DEBUG] Customer Name: {customer_name}")

# #         if not customer_name:
# #             return "Failed: No customer/payer found in billing data"


# #         # Date conversion
# #         date = ar_details["g_creation_time"]
# #         datetimes = date / 1000.0

# #         # Define GMT+4
# #         gmt_plus_4 = timezone(timedelta(hours=4))
# #         dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
# #         formatted_date = dt.strftime('%Y-%m-%d')

# #         frappe.logger().info(f"[JE DEBUG] Formatted Posting Date: {formatted_date}")
# #         # frappe.msgprint(f"[DEBUG] Posting Date: {formatted_date}")

# #         # Initialize JE entries
# #         je_entries = []

# #         # #Duplicate check: same Employee, Date, and Amount
# #         # existing_je = frappe.db.exists(
# #         #     "Journal Entry",
# #         #     {
# #         #         "posting_date": formatted_date,
# #         #         "docstatus": 1,  # submitted
# #         #         "user_remark": f"AR Settlement for Bill No: {bill_no}"
# #         #     }
# #         # )
# #         # if existing_je:
# #         #     frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
# #         #     return f"Skipped: Journal Entry {existing_je} already exists"

# #         #Credit the payer (customer)
# #         credit_entry = {
# #             "account": debit_account,  # Update to actual customer account if dynamic
# #             "party_type": "Customer",
# #             "party": customer,
# #             "credit_in_account_currency": rec_amount,
# #             "debit_in_account_currency": 0
# #         }
# #         je_entries.append(credit_entry)
# #         frappe.logger().info(f"[JE DEBUG] Added Credit Entry: {credit_entry}")

# #         #Debit each payment mode from payment_details
# #         for payment in payment_details:
# #             mode = payment.get("payment_mode_code", "").lower()
# #             amount = payment.get("amount", 0)

# #             frappe.logger().info(f"[JE DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")
# #             # frappe.msgprint(f"[DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")

# #             if amount <= 0:
# #                 frappe.logger().warning(f"[JE DEBUG] Skipping mode {mode} as amount is 0")
# #                 continue

# #             if mode == "cash":
# #                 account = cash_account
# #             elif mode in ["upi", "card", "bank","neft"]:
# #                 account = bank_account
# #             elif mode == "credit":
# #                 account = debit_account
# #             else:
# #                 account = bank_account

# #             debit_entry = {
# #                 "account": account,
# #                 "debit_in_account_currency": amount,
# #                 "credit_in_account_currency": 0
# #             }
# #             je_entries.append(debit_entry)
# #             frappe.logger().info(f"[JE DEBUG] Added Debit Entry: {debit_entry}")
# #             # frappe.msgprint(f"[DEBUG] Debit Entry: {debit_entry}")

# #         frappe.logger().info(f"[JE DEBUG] Final JE Entries: {je_entries}")
# #         # frappe.msgprint(f"[DEBUG] Final JE Entries: {je_entries}")

# #         #Create the Journal Entry
# #         je_doc = frappe.get_doc({
# #             "doctype": "Journal Entry",
# #             "posting_date": formatted_date,
# #             "accounts": je_entries,
# #             "naming_series": "KX-JV-.YYYY.-",
# #             "user_remark": f"Due Settlement for Bill No: {bill_no}",
# #             "custom_bill_category": "DUE SETTLEMENT",
# #             "custom_bill_number": bill_no,
# #             "custom_uhid": uhid,
# #             "custom_payer_name": customer,
# #             "custom_receipt_no": receipt_no,
# #             "custom_admission_id": admission_id
# #         })
# #         je_doc.insert(ignore_permissions=True)
# #         frappe.db.commit()
# #         je_doc.submit()
# #         frappe.logger().info(f"[JE DEBUG] Journal Entry {je_doc.name} created successfully.")
# #         # frappe.msgprint(f"[DEBUG] Journal Entry {je_doc.name} created successfully.")

# #         return je_doc.name

# #     except Exception as e:
# #         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
# #         frappe.logger().error(f"[JE DEBUG] Exception: {str(e)}")
# #         # frappe.msgprint(f"[DEBUG] Error: {str(e)}")
# #         return f"Failed to create Journal Entry: {str(e)}"

# # def get_or_create_customer(customer_name, payer_type=None):
# #     # If payer type is cash, don't create a customer
# #     if payer_type and payer_type.lower() == "cash":
# #         return None
# #     # Check if the customer already exists
# #     existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":payer_type})
# #     if existing_customer:
# #         return existing_customer

# #     # Determine customer group based on payer_type
# #     if payer_type:
# #         payer_type = payer_type.lower()
# #         if payer_type == "insurance":
# #             customer_group = "Insurance"
# #         elif payer_type == "cash":
# #             customer_group = "Cash"
# #         elif payer_type == "credit":
# #             customer_group = "Credit"
# #         else:
# #             customer_group = "Individual"  # default fallback
# #     else:
# #         customer_group = "Individual"

# #     # Create new customer
# #     customer = frappe.get_doc({
# #         "doctype": "Customer",
# #         "customer_name": customer_name,
# #         "customer_group": customer_group,
# #         "territory": "All Territories"
# #     })
# #     customer.insert(ignore_permissions=True)
# #     frappe.db.commit()

# #     return customer.name


# import frappe
# import requests
# import json
# from frappe.utils import nowdate
# from datetime import datetime
# from frappe.utils import getdate, add_days, cint
# from datetime import datetime, timedelta, time, timezone
# from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# billing_type = "DUE SETTLEMENT"
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

# def fetch_advance_billing(jwt_token, from_date, to_date):
#     headers_billing = {
#         "Content-Type": "application/json",
#         "clientCode": "ALNILE_THINKNXG_FI",
#         "integrationKey": "BILLING_DUE_SETTLEMENT",
#         "Authorization": f"Bearer {jwt_token}"
#     }
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")


# @frappe.whitelist()
# def main():
#     try:
#         jwt_token = get_jwt_token()
#         frappe.log("JWT Token fetched successfully.")
#         # from_date = 1672531200000  
#         # to_date = 1966962420000    
#         # Fetch dynamic date and number of days from settings
#         settings = frappe.get_single("Karexpert Settings")

#         # Get to_date from settings or fallback to nowdate() - 4 days
#         to_date_raw = settings.get("date")
#         if to_date_raw:
#             t_date = getdate(to_date_raw)
#         else:
#             t_date = getdate(add_days(nowdate(), -2))

#         # Get no_of_days from settings and calculate from_date
#         no_of_days = cint(settings.get("no_of_days") or 3)  # default 3 days if not set
#         f_date = getdate(add_days(t_date, -no_of_days))

#         # Convert to timestamps (GMT+4)
#         gmt_plus_4 = timezone(timedelta(hours=4))
#         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
#         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

#         billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
#         frappe.log("Due settlement data fetched successfully.")

#         for billing in billing_data.get("jsonResponse", []):
#             create_journal_entry(billing["due_settlement"])

#     except Exception as e:
#         frappe.log_error(f"Error: {e}")

# if __name__ == "__main__":
#     main()

# def create_journal_entry(billing_data):
#     try:
#         frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")
#         # frappe.msgprint(f"[DEBUG] Received billing_data: {billing_data}")
        
#         ar_details = billing_data
#         bill_no = ar_details.get("bill_no")
#         admission_id = ar_details.get("admissionId")
#         receipt_no = ar_details.get("receipt_no")
#         uhid = ar_details.get("uhId")
#         payment_details = ar_details.get("payment_transaction_details", [])
#         rec_amount = ar_details.get("received_amount")
#         customer_name = ar_details.get("payer_name") or billing_data.get("customer")
#         payer_type = ar_details.get("payer_type") or billing_data["payer_type"]
#         customer = get_or_create_customer(customer_name,payer_type)
        
#         # --- Fetch accounts dynamically from Company ---
#         company = frappe.defaults.get_user_default("Company")
#         company_doc = frappe.get_doc("Company", company)

#         debit_account = company_doc.default_receivable_account
#         credit_account = company_doc.default_income_account
#         cash_account = company_doc.default_cash_account
#         bank_account = company_doc.default_bank_account
#         frappe.logger().info(f"[JE DEBUG] Bill No: {bill_no}")
#         # frappe.msgprint(f"[DEBUG] Bill No: {bill_no}")
#         frappe.logger().info(f"[JE DEBUG] Customer Name: {customer_name}")
#         # frappe.msgprint(f"[DEBUG] Customer Name: {customer_name}")

#         if not customer_name:
#             return "Failed: No customer/payer found in billing data"


#         # Date conversion
#         date = ar_details["g_creation_time"]
#         datetimes = date / 1000.0

#         # Define GMT+4
#         gmt_plus_4 = timezone(timedelta(hours=4))
#         dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
#         formatted_date = dt.strftime('%Y-%m-%d')

#         frappe.logger().info(f"[JE DEBUG] Formatted Posting Date: {formatted_date}")
#         # frappe.msgprint(f"[DEBUG] Posting Date: {formatted_date}")

#         # Initialize JE entries
#         je_entries = []

#         # #Duplicate check: same Employee, Date, and Amount
#         # existing_je = frappe.db.exists(
#         #     "Journal Entry",
#         #     {
#         #         "posting_date": formatted_date,
#         #         "docstatus": 1,  # submitted
#         #         "user_remark": f"AR Settlement for Bill No: {bill_no}"
#         #     }
#         # )
#         # if existing_je:
#         #     frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
#         #     return f"Skipped: Journal Entry {existing_je} already exists"

#                 #Credit the payer (customer)
#             # Credit the payer
#         if customer:
#             # is due:true
#             credit_entry = {
#                 "account": "Due Ledger - AN", 
#                 # "party_type": "Customer",
#                 # "party": customer,
#                 "credit_in_account_currency": rec_amount,
#                 "debit_in_account_currency": 0
#             }
#             je_entries.append(credit_entry)
#             frappe.logger().info(f"[JE DEBUG] Added Credit Entry to Customer: {credit_entry}")
#         else:
#             # is due : false
#             credit_entry = {
#                 "account": "Due Ledger - AN", 
#                 "debit_in_account_currency": 0,
#                 "credit_in_account_currency": rec_amount,
#                 # "party_type": "Customer",
#                 # "party": customer,
#             }
#             je_entries.append(credit_entry)
#             frappe.logger().info(f"[JE DEBUG] Added Credit Entry to Due: {credit_entry}")


#         #Debit each payment mode from payment_details
#         for payment in payment_details:
#             mode = payment.get("payment_mode_code", "").lower()
#             amount = payment.get("amount", 0)

#             frappe.logger().info(f"[JE DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")
#             # frappe.msgprint(f"[DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")

#             if amount <= 0:
#                 frappe.logger().warning(f"[JE DEBUG] Skipping mode {mode} as amount is 0")
#                 continue

#             if mode == "cash":
#                 account = cash_account
#             elif mode in ["upi", "card", "bank","neft"]:
#                 account = bank_account
#             elif mode == "credit":
#                 account = bank_account
#             else:
#                 account = bank_account

#             debit_entry = {
#                 "account": account,
#                 "debit_in_account_currency": amount,
#                 "credit_in_account_currency": 0,
#                 # "party_type": "Customer",
#                 # "party": customer    
#              }

#             je_entries.append(debit_entry)
#             frappe.logger().info(f"[JE DEBUG] Added Debit Entry: {debit_entry}")
#             # frappe.msgprint(f"[DEBUG] Debit Entry: {debit_entry}")

#         frappe.logger().info(f"[JE DEBUG] Final JE Entries: {je_entries}")
#         # frappe.msgprint(f"[DEBUG] Final JE Entries: {je_entries}")

#         #Create the Journal Entry
#         je_doc = frappe.get_doc({
#             "doctype": "Journal Entry",
#             "posting_date": formatted_date,
#             "accounts": je_entries,
#             "naming_series": "KX-JV-.YYYY.-",
#             "user_remark": f"Due Settlement for Bill No: {bill_no}",
#             "custom_bill_category": "DUE SETTLEMENT",
#             "custom_bill_number": bill_no,
#             "custom_uhid": uhid,
#             "custom_payer_name": customer,
#             "custom_receipt_no": receipt_no,
#             "custom_admission_id": admission_id
#         })
#         je_doc.insert(ignore_permissions=True)
#         frappe.db.commit()
#         je_doc.submit()
#         frappe.logger().info(f"[JE DEBUG] Journal Entry {je_doc.name} created successfully.")
#         # frappe.msgprint(f"[DEBUG] Journal Entry {je_doc.name} created successfully.")

#         return je_doc.name

#     except Exception as e:
#         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
#         frappe.logger().error(f"[JE DEBUG] Exception: {str(e)}")
#         # frappe.msgprint(f"[DEBUG] Error: {str(e)}")
#         return f"Failed to create Journal Entry: {str(e)}"

# def get_or_create_customer(customer_name, payer_type=None):
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

# # import frappe
# # import requests
# # import json
# # from frappe.utils import nowdate
# # from datetime import datetime
# # from frappe.utils import getdate, add_days, cint
# # from datetime import datetime, timedelta,time,timezone
# # from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# # billing_type = "DUE SETTLEMENT"
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
# #         "integrationKey": "BILLING_DUE_SETTLEMENT",
# #         "Authorization": f"Bearer {jwt_token}"
# #     }
# #     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
# #     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
# #     if response.status_code == 200:
# #         return response.json()
# #     else:
# #         frappe.throw(f"Failed to due settlement data: {response.status_code} - {response.text}")
# # @frappe.whitelist()
# # def main():
# #     try:
# #         jwt_token = get_jwt_token()
# #         frappe.log("JWT Token fetched successfully.")

# #         # from_date = 1672531200000  
# #         # to_date = 1966962420000    
# #         # Fetch dynamic date and number of days from settings
# #         settings = frappe.get_single("Karexpert Settings")
# #         # Get to_date from settings or fallback to nowdate() - 4 days
# #         to_date_raw = settings.get("date")
# #         if to_date_raw:
# #             t_date = getdate(to_date_raw)
# #         else:
# #             t_date = add_days(nowdate(), -4)

# #         # Get no_of_days from settings and calculate from_date
# #         no_of_days = cint(settings.get("no_of_days") or 25)  # default 3 days if not set
# #         f_date = add_days(t_date, -no_of_days)
# #          # Define GMT+4 timezone
# #         gmt_plus_4 = timezone(timedelta(hours=4))

# #         # Convert to timestamps in milliseconds for GMT+4
# #         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
# #         print("---f", from_date)
# #         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
# #         print("----t", to_date)

# #         billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
# #         frappe.log("Due settlement data fetched successfully.")

# #         for billing in billing_data.get("jsonResponse", []):
# #             create_journal_entry(billing["due_settlement"])

# #     except Exception as e:
# #         frappe.log_error(f"Error: {e}")

# # if __name__ == "__main__":
# #     main()

# # def create_journal_entry(billing_data):
# #     try:
# #         bill_no = billing_data["bill_no"]

# #         payment_details = billing_data.get("payment_transaction_details", [])
        
# #         # --- Fetch accounts dynamically from Company ---
# #         company = frappe.defaults.get_user_default("Company")
# #         company_doc = frappe.get_doc("Company", company)

# #         debit_account = company_doc.default_receivable_account
# #         credit_account = company_doc.default_income_account
# #         cash_account = company_doc.default_cash_account
# #         bank_account = company_doc.default_bank_account
# #         write_off_account = company_doc.write_off_account

# #         authorized_amount = billing_data.get("authorized_amount", 0)
# #         payer_amounts = billing_data.get("received_amount", 0)
# #         payer_amount = authorized_amount + payer_amounts

# #         # Initialize journal entry rows
# #         je_entries = []
# #         je_entries.append({
# #                 "account": "Due Ledger - AN",
# #                 "debit_in_account_currency": 0,
# #                 "credit_in_account_currency": payer_amount,
# #             })
# #         # Handling Credit Payment Mode
# #         credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
# #         if authorized_amount>0:
# #             je_entries.append({
# #                 "account": "Debtors - AN",  # Replace with actual debtors account
# #                 "debit_in_account_currency": authorized_amount,
# #                 "credit_in_account_currency": 0,
# #             })
            

# #         # Handling Cash Payment Mode
# #         for payment in payment_details:
# #             if payment["payment_mode_code"].lower() == "cash":
# #                 je_entries.append({
# #                     "account": cash_account,  # Replace with actual cash account
# #                     "debit_in_account_currency": payment["amount"],
# #                     "credit_in_account_currency": 0
# #                 })

# #         # Handling Other Payment Modes (UPI, Card, etc.)
# #         bank_payment_total = sum(
# #             p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "credit","IP ADVANCE"]
# #         )
# #         if bank_payment_total > 0:
# #             je_entries.append({
# #                 "account": bank_account,  # Replace with actual bank account
# #                 "debit_in_account_currency": bank_payment_total,
# #                 "credit_in_account_currency": 0
# #             })

# #         # Create Journal Entry if there are valid transactions
# #         if je_entries:
# #             je_doc = frappe.get_doc({
# #                 "doctype": "Journal Entry",
# #                 "posting_date": nowdate(),
# #                 "accounts": je_entries,
# #                 "user_remark": f"Due Settlement of: {bill_no}"
# #             })
# #             je_doc.insert(ignore_permissions=True)
# #             frappe.db.commit()

# #             # Link Journal Entry to Sales Invoice
# #             # frappe.db.set_value("Sales Invoice", sales_invoice_name, "journal_entry", je_doc.name)
# #             frappe.msgprint(f"Journal Entry {je_doc.name} created successfully.")
    
# #     except Exception as e:
# #         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
# #         return f"Failed to create Journal Entry: {str(e)}"



# import frappe
# import requests
# import json
# from frappe.utils import nowdate
# from datetime import datetime
# from frappe.utils import getdate, add_days, cint
# from datetime import datetime, timedelta, time, timezone
# from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

# billing_type = "DUE SETTLEMENT"
# settings = frappe.get_single("Karexpert Settings")
# TOKEN_URL = settings.get("token_url")
# BILLING_URL = settings.get("billing_url")

# # Fetch row details based on billing type
# billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
#                                 ["client_code", "integration_key", "x_api_key"], as_dict=True)

# headers_token = fetch_api_details(billing_type)


# def fetch_advance_billing(jwt_token, from_date, to_date, headers):
#     payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
#     headers_billing = headers.copy()
#     headers_billing["Authorization"] = f"Bearer {jwt_token}"

#     response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")


# @frappe.whitelist()
# def main():
#     try:
#         settings = frappe.get_single("Karexpert Settings")

#         # Collect all facility IDs from child table
#         facility_list = [row.facility_id for row in settings.get("facility_id_details") or [] if row.facility_id]

#         if not facility_list:
#             frappe.throw("No facility IDs found in Karexpert Settings.")

#         # Prepare date range
#         to_date_raw = settings.get("date")
#         t_date = getdate(to_date_raw) if to_date_raw else getdate(add_days(nowdate(), 0))
#         no_of_days = cint(settings.get("no_of_days") or 25)
#         f_date = getdate(add_days(t_date, -no_of_days))

#         # Convert to timestamps (GMT+4)
#         gmt_plus_4 = timezone(timedelta(hours=4))
#         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
#         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

#         all_billing_data = []

#         # Loop through each facility
#         for row in settings.get("facility_id_details") or []:
#             facility_id = row.facility_id
#             if not facility_id:
#                 continue

#             # Prepare headers for this facility
#             billing_row = frappe.get_value(
#                 "Karexpert  Table",
#                 {"billing_type": "DUE SETTLEMENT"},
#                 ["client_code", "integration_key", "x_api_key"],
#                 as_dict=True
#             )

#             headers = {
#                 "Content-Type": "application/json",
#                 "clientCode": billing_row["client_code"],
#                 "integrationKey": billing_row["integration_key"],
#                 "facilityId": facility_id,
#                 "messageType": "request",
#                 "x-api-key": billing_row["x_api_key"]
#             }

#             # Fetch JWT for this facility
#             jwt_token = get_jwt_token_for_headers(headers)

#             frappe.log(f"Fetching AR bill settlement for Facility ID: {facility_id}")
#             print("Fetching aAR bill settlement for Facility ID",facility_id)
#             billing_data = fetch_advance_billing(jwt_token, from_date, to_date, headers)

#             if billing_data and "jsonResponse" in billing_data:
#                 all_billing_data.extend(billing_data["jsonResponse"])
#             else:
#                 frappe.log(f"No data returned for {facility_id}")

#         # ✅ Process all collected billing data
#         for billing in all_billing_data:
#             create_journal_entry(billing['due_settlement'])

#         frappe.log("All facility AR bill settlement data processed successfully.")

#     except Exception as e:
#         frappe.log_error(f"Error in AR bill settlement Fetch: {e}")


# def get_jwt_token_for_headers(headers):
#     """
#     Fetch JWT token using the provided headers dict.
#     """
#     try:
#         response = requests.post(TOKEN_URL, headers=headers, timeout=10)
#         if response.status_code == 200:
#             return response.json().get("jwttoken")
#         else:
#             frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")
#     except requests.exceptions.RequestException as e:
#         frappe.throw(f"JWT request failed: {e}")

# if __name__ == "__main__":
#     main()

# @frappe.whitelist()
# def create_journal_entry(billing_data):
#     try:
#         frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")
#         # frappe.msgprint(f"[DEBUG] Received billing_data: {billing_data}")
        
#         ar_details = billing_data
#         bill_no = ar_details.get("bill_no")
#         admission_id = ar_details.get("admissionId")
#         receipt_no = ar_details.get("receipt_no")
#         uhid = ar_details.get("uhId")
#         payment_details = ar_details.get("payment_transaction_details", [])
#         rec_amount = ar_details.get("received_amount")
#         customer_name = ar_details.get("payer_name") or billing_data.get("customer")
#         payer_type = ar_details.get("payer_type") or billing_data["payer_type"]
#         customer = get_or_create_customer(customer_name,payer_type)
#         # --- Fetch accounts dynamically from Company ---
#         company = frappe.defaults.get_user_default("Company")
#         company_doc = frappe.get_doc("Company", company)

#         debit_account = company_doc.default_receivable_account
#         credit_account = company_doc.default_income_account
#         cash_account = company_doc.default_cash_account
#         bank_account = company_doc.default_bank_account
#         frappe.logger().info(f"[JE DEBUG] Bill No: {bill_no}")
#         # frappe.msgprint(f"[DEBUG] Bill No: {bill_no}")
#         frappe.logger().info(f"[JE DEBUG] Customer Name: {customer_name}")
#         # frappe.msgprint(f"[DEBUG] Customer Name: {customer_name}")

#         if not customer_name:
#             return "Failed: No customer/payer found in billing data"


#         # Date conversion
#         date = ar_details["g_creation_time"]
#         datetimes = date / 1000.0

#         # Define GMT+4
#         gmt_plus_4 = timezone(timedelta(hours=4))
#         dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
#         formatted_date = dt.strftime('%Y-%m-%d')

#         frappe.logger().info(f"[JE DEBUG] Formatted Posting Date: {formatted_date}")
#         # frappe.msgprint(f"[DEBUG] Posting Date: {formatted_date}")

#         # Initialize JE entries
#         je_entries = []

#         # #Duplicate check: same Employee, Date, and Amount
#         # existing_je = frappe.db.exists(
#         #     "Journal Entry",
#         #     {
#         #         "posting_date": formatted_date,
#         #         "docstatus": 1,  # submitted
#         #         "user_remark": f"AR Settlement for Bill No: {bill_no}"
#         #     }
#         # )
#         # if existing_je:
#         #     frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
#         #     return f"Skipped: Journal Entry {existing_je} already exists"

#         #Credit the payer (customer)
#         credit_entry = {
#             "account": debit_account,  # Update to actual customer account if dynamic
#             "party_type": "Customer",
#             "party": customer,
#             "credit_in_account_currency": rec_amount,
#             "debit_in_account_currency": 0
#         }
#         je_entries.append(credit_entry)
#         frappe.logger().info(f"[JE DEBUG] Added Credit Entry: {credit_entry}")

#         #Debit each payment mode from payment_details
#         for payment in payment_details:
#             mode = payment.get("payment_mode_code", "").lower()
#             amount = payment.get("amount", 0)

#             frappe.logger().info(f"[JE DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")
#             # frappe.msgprint(f"[DEBUG] Processing Payment Mode: {mode} | Amount: {amount}")

#             if amount <= 0:
#                 frappe.logger().warning(f"[JE DEBUG] Skipping mode {mode} as amount is 0")
#                 continue

#             if mode == "cash":
#                 account = cash_account
#             elif mode in ["upi", "card", "bank","neft"]:
#                 account = bank_account
#             elif mode == "credit":
#                 account = debit_account
#             else:
#                 account = bank_account

#             debit_entry = {
#                 "account": account,
#                 "debit_in_account_currency": amount,
#                 "credit_in_account_currency": 0
#             }
#             je_entries.append(debit_entry)
#             frappe.logger().info(f"[JE DEBUG] Added Debit Entry: {debit_entry}")
#             # frappe.msgprint(f"[DEBUG] Debit Entry: {debit_entry}")

#         frappe.logger().info(f"[JE DEBUG] Final JE Entries: {je_entries}")
#         # frappe.msgprint(f"[DEBUG] Final JE Entries: {je_entries}")

#         #Create the Journal Entry
#         je_doc = frappe.get_doc({
#             "doctype": "Journal Entry",
#             "posting_date": formatted_date,
#             "accounts": je_entries,
#             "naming_series": "KX-JV-.YYYY.-",
#             "user_remark": f"Due Settlement for Bill No: {bill_no}",
#             "custom_bill_category": "DUE SETTLEMENT",
#             "custom_bill_number": bill_no,
#             "custom_uhid": uhid,
#             "custom_payer_name": customer,
#             "custom_receipt_no": receipt_no,
#             "custom_admission_id": admission_id
#         })
#         je_doc.insert(ignore_permissions=True)
#         frappe.db.commit()
#         je_doc.submit()
#         frappe.logger().info(f"[JE DEBUG] Journal Entry {je_doc.name} created successfully.")
#         # frappe.msgprint(f"[DEBUG] Journal Entry {je_doc.name} created successfully.")

#         return je_doc.name

#     except Exception as e:
#         frappe.log_error(f"Error creating Journal Entry: {str(e)}")
#         frappe.logger().error(f"[JE DEBUG] Exception: {str(e)}")
#         # frappe.msgprint(f"[DEBUG] Error: {str(e)}")
#         return f"Failed to create Journal Entry: {str(e)}"

# def get_or_create_customer(customer_name, payer_type=None):
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

        # #Duplicate check: same Employee, Date, and Amount
        # existing_je = frappe.db.exists(
        #     "Journal Entry",
        #     {
        #         "posting_date": formatted_date,
        #         "docstatus": 1,  # submitted
        #         "user_remark": f"AR Settlement for Bill No: {bill_no}"
        #     }
        # )
        # if existing_je:
        #     frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
        #     return f"Skipped: Journal Entry {existing_je} already exists"

                #Credit the payer (customer)
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
            elif mode in ["upi", "card", "bank","neft"]:
                account = bank_account
            elif mode == "credit":
                account = bank_account
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