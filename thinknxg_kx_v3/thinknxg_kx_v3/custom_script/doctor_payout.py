
import frappe
import requests
import json
import re
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "DOCTOR PAYOUT"
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

def fetch_doctor_payout(jwt_token, from_date, to_date):
    headers_billing = {
        "Content-Type": "application/json",
        "clientCode": "ALNILE_THINKNXG_FI",
        "integrationKey": "DOCTOR_PAYOUT",
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch doctor payout data: {response.status_code} - {response.text}")
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
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

        billing_data = fetch_doctor_payout(jwt_token, from_date, to_date)
        frappe.log("Doctor payout data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry(billing)

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

@frappe.whitelist()
def create_journal_entry(billing_data):
    try:
        frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {billing_data}")
        # frappe.msgprint(f"[DEBUG] Received billing_data: {billing_data}")
        
        payout_detail = billing_data.get("doctor_payout", [])
        # bill_no = ar_details.get("bill_no")
        # payment_details = ar_details.get("payment_detail", [])
        customer_name = payout_detail.get("payout_name") or billing_data.get("customer")

        frappe.logger().info(f"[JE DEBUG] Customer Name: {customer_name}")
        # frappe.msgprint(f"[DEBUG] Customer Name: {customer_name}")


        if not customer_name:
            return "Failed: No customer/payer found in payout data"

        # Total amount from payment details
        # total_amount = sum(p.get("net_amount", 0) for p in payout_detail)
        total_amount = payout_detail.get("net_amount", 0)
        frappe.logger().info(f"[JE DEBUG] Total Payment Amount: {total_amount}")
        # frappe.msgprint(f"[DEBUG] Total Payment Amount: {total_amount}")

        if total_amount <= 0:
            return f"Failed: No valid payment amount"

        # Date conversion
        date = payout_detail["g_creation_time"]
        datetimes = date / 1000.0

        # Define GMT+4
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
        formatted_date = dt.strftime('%Y-%m-%d')

        frappe.logger().info(f"[JE DEBUG] Formatted Posting Date: {formatted_date}")
        # frappe.msgprint(f"[DEBUG] Posting Date: {formatted_date}")

        # Initialize JE entries
        je_entries = []
        # Clean API name: remove salutation, strip spaces, convert to upper case
        raw_name = payout_detail.get("payout_name", "")
        clean_name = re.sub(r'^(Dr|Mr|Mrs|Ms)\s+', '', raw_name, flags=re.IGNORECASE).strip().upper()

        # Fetch employee ID ignoring case
        employee_id = frappe.db.get_value(
            "Employee", 
            {"employee_name": clean_name}, 
            "name"
        )

        if not employee_id:
            return f"Failed: No Employee found for {raw_name}"
        #Duplicate check: same Employee, Date, and Amount
        existing_je = frappe.db.exists(
            "Journal Entry",
            {
                "posting_date": formatted_date,
                "docstatus": 1,  # submitted
                "user_remark": f"Doctor Payout for: {customer_name}"
            }
        )
        if existing_je:
            frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
            return f"Skipped: Journal Entry {existing_je} already exists"
        #Debit the payer (customer)
        debit_entry = {
            "account": "Doctor Payout - AN",  # Update to actual customer account if dynamic
            "party_type": "Employee",
            "party": employee_id,

            "credit_in_account_currency": 0,
            "debit_in_account_currency": total_amount
        }
        je_entries.append(debit_entry)
        frappe.logger().info(f"[JE DEBUG] Added Credit Entry: {debit_entry}")
        # frappe.msgprint(f"[DEBUG] Credit Entry: {credit_entry}")

        #Credit Doctor Payout Payable
        credit_entry = {
            "account": "Doctor Payout Payable - AN",  # Replace with actual payable account
            "debit_in_account_currency": 0,
            "credit_in_account_currency": total_amount
        }
        je_entries.append(credit_entry)
        frappe.logger().info(f"[JE DEBUG] Added Debit Entry: {credit_entry}")

        frappe.logger().info(f"[JE DEBUG] Final JE Entries: {je_entries}")
        # frappe.msgprint(f"[DEBUG] Final JE Entries: {je_entries}")

        #Create the Journal Entry
        je_doc = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "accounts": je_entries,
            "user_remark": f"Doctor Payout for: {customer_name}",
            "custom_bill_category": "DOCTOR PAYOUT"
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