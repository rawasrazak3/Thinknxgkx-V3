
import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "GET MAIN STORE CONSUMPTION"
# billing_type = "GET STOCK CONSUMPTION"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert Table", {"billing_type": billing_type},
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
        "clientCode": "ALNILE_THINKNXG_MM",
        # "integrationKey": "GET_MAIN_STORE_CONSUMPTION",
        "integrationKey": "GET_STOCK_CONSUMPTION",
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch stock consumption data: {response.status_code} - {response.text}")
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
        f_date = add_days(t_date, -no_of_days)
         # Define GMT+4 timezone
        gmt_plus_4 = timezone(timedelta(hours=4))

        # Convert to timestamps in milliseconds for GMT+4
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

        billing_data = fetch_advance_billing(jwt_token, from_date, to_date)
        frappe.log("Stock consumption data fetched successfully.")

        # Process billing data per facility
        grouped_data = {}
        for record in billing_data.get("jsonResponse", []):
            transfer_type = record.get("transactionType", "").lower()
            if transfer_type == "store consumption":
                key = record.get("transactionId")
                category = "STORE CONSUMPTION"
            else:
                continue

            if not key:
                frappe.log(f"Missing key for record {record.get('id')}")
                continue

            if key not in grouped_data:
                grouped_data[key] = {"records": [], "category": category}
            grouped_data[key]["records"].append(record)

        for key, data in grouped_data.items():
            create_journal_entry_from_billing_group(key, data["records"], data["category"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

@frappe.whitelist()
def create_journal_entry_from_billing_group(key, records, category):
    try:
        if frappe.db.exists("Journal Entry", {"custom_issue_no": key, "custom_bill_category": category, "docstatus": 1}):
            frappe.log(f"Journal Entry for Issueno {key} already exists.")
            return
        frappe.logger().info(f"[JE DEBUG] Incoming billing_data: {records}")
        # frappe.msgprint(f"[DEBUG] Received billing_data: {billing_data}")
        
        first_record = records[0]
        transfer_type = first_record.get("transfer_type")
        bill_no = first_record.get("transactionId")
        facility_name = first_record.get("facility_name")
        
         # --- Fetch accounts dynamically from Company ---
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)

        debit_account = company_doc.default_receivable_account
        credit_account = company_doc.default_income_account
        bank_account = company_doc.default_bank_account
        stock_acc = "Stock In Hand - AN"
        write_off_account = "Write Off - AN"
        consumption_acc = "Store Consumption - AN"
        vat_account = "VAT 5% - AN"
        default_expense_account = company_doc.default_expense_account
        default_stock_in_hand = company_doc.default_inventory_account

        # Total amount from payment details
        total_value = sum([float(r.get("ueprValue", 0)) for r in records])
        frappe.logger().info(f"[JE DEBUG] Total Payment Amount: {total_value}")
        # frappe.msgprint(f"[DEBUG] Total Payment Amount: {total_amount}")

        if total_value <= 0:
            return f"Failed: No valid payment amount for bill no {bill_no}"

        # Date conversion
        date = first_record["g_creation_time"]
        datetimes = date / 1000.0

        # Define GMT+4
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
        formatted_date = dt.strftime('%Y-%m-%d')

        frappe.logger().info(f"[JE DEBUG] Formatted Posting Date: {formatted_date}")
        # frappe.msgprint(f"[DEBUG] Posting Date: {formatted_date}")

        # Initialize JE entries
        je_entries = []
        #Duplicate check: same Employee, Date, and Amount
        existing_je = frappe.db.exists(
            "Journal Entry",
            {
                "docstatus": 1,  # submitted
                "custom_bill_number": bill_no
            }
        )
        if existing_je:
            frappe.logger().info(f"[JE DEBUG] Duplicate found, skipping JE creation. Existing JE: {existing_je}")
            return f"Skipped: Journal Entry {existing_je} already exists"
        #Credit the payer (customer)
        credit_entry = {
            "account": stock_acc,  
            "credit_in_account_currency": total_value,
            "debit_in_account_currency": 0
        }
        je_entries.append(credit_entry)
        frappe.logger().info(f"[JE DEBUG] Added Credit Entry: {credit_entry}")
        # frappe.msgprint(f"[DEBUG] Credit Entry: {credit_entry}")
        debit_entry = {
            "account": consumption_acc,
            "debit_in_account_currency": total_value,
            "credit_in_account_currency": 0
        }
        je_entries.append(debit_entry)
        frappe.logger().info(f"[JE DEBUG] Added Debit Entry: {debit_entry}")
        

        frappe.logger().info(f"[JE DEBUG] Final JE Entries: {je_entries}")
        # frappe.msgprint(f"[DEBUG] Final JE Entries: {je_entries}")

        #Create the Journal Entry
        je_doc = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "custom_bill_number":bill_no,
            "accounts": je_entries,
            "user_remark": f" Stock Consumption for Bill No: {bill_no}",
            "custom_bill_category": "STOCK CONSUMPTION"
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