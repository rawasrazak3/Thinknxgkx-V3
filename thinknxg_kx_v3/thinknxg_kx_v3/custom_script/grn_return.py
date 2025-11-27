import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "GRN RETURN DETAIL"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
RETURN_URL = settings.get("billing_url")
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

def fetch_grn_returns(jwt_token, from_date, to_date):
    headers_return = {
        "Content-Type": "application/json",
        "clientCode": "METRO_THINKNXG_MM",
        "integrationKey": "GRN_RETURN_DETAIL",
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(RETURN_URL, headers=headers_return, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch GRN return data: {response.status_code} - {response.text}")

def group_return_items_by_drReturnNo(return_items):
    grouped_returns = {}
    for item in return_items:
        dr_return_no = item["drReturnNo"]
        if dr_return_no not in grouped_returns:
            grouped_returns[dr_return_no] = {
                "items": [],
                "total_net_purchase_value": 0.0,
                "total_tax": 0.0,
                "first_item": item  # Store the first item for common fields
            }
        
        # Convert string values to float
        net_purchase_value = float(item.get("netPurchaseValue", 0) or 0.0)
        total_qty = float(item.get("returnQuantity",0) or 0.0)
        total_tax = float(item.get("tax", 0) or 0.0)
        tax = total_tax * total_qty
        
        grouped_returns[dr_return_no]["items"].append(item)
        grouped_returns[dr_return_no]["total_net_purchase_value"] += net_purchase_value
        grouped_returns[dr_return_no]["total_tax"] += tax
    
    return grouped_returns


def get_default_warehouse():
    return frappe.db.get_single_value("Stock Settings", "default_warehouse") or "Stores - AN"

def get_existing_supplier(supplier_code):
    supplier_name = frappe.db.get_value("Supplier", {"custom_supplier_code": supplier_code}, "name")
    if not supplier_name:
        frappe.log_error(f"Supplier with code '{supplier_code}' not found.", "Missing Supplier")
        return None
    return supplier_name

def create_journal_entry_for_return(grouped_return):
    dr_return_no = grouped_return["first_item"]["drReturnNo"]
    print("--return no--",dr_return_no)
    dr_no = grouped_return["first_item"]["drNo"]
    supplier = grouped_return["first_item"].get("supplierCode")
    supplier_name = get_existing_supplier(supplier)
    if not supplier_name:
        frappe.log(f"Supplier {supplier} not found, skipping return {dr_return_no}")
        return
    store_name = grouped_return["first_item"]["storeName"]
    # Fetch Supplier Name
    supplier_doc = frappe.get_doc("Supplier", supplier_name)
    supplier_n = supplier_doc.supplier_name

    # Check if journal entry already exists
    existing_jv = frappe.db.exists("Journal Entry", {"custom_return_no": dr_return_no, "docstatus":1})
    if existing_jv:
        frappe.log(f"Journal Entry for drReturnNo {dr_return_no} already exists.")
        return

    # Get posting date/time from return data
    date_ts = float(grouped_return["first_item"]["g_creation_time"])
    datetimes = date_ts / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    posting_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')

    total_amount = grouped_return["total_net_purchase_value"] + grouped_return["total_tax"]
    print("---amount--",grouped_return["total_net_purchase_value"])
    print("---tax---",grouped_return["total_tax"])
    if total_amount <= 0:
        frappe.log(f"Total amount for drReturnNo {dr_return_no} is zero or negative, skipping.")
        return

    # Get company from linked invoice if needed, or hardcode
    company = frappe.defaults.get_user_default("Company")
    
    # Fetch default accounts
    stock_account = frappe.db.get_value("Account", {"account_name": "Stock In Hand", "company": company})
    print("stock",stock_account)
    creditor_account = frappe.db.get_value("Account", {"account_name": "Creditors", "company": company})
    print("creditor",creditor_account)
    if not stock_account or not creditor_account:
        frappe.log_error("Stock or Creditors account not found for company: " + company)
        return
    # Find original purchase invoice based on drNo
    original_invoice = frappe.get_all(
        "Journal Entry",
        filters={"custom_grn_number": dr_no, "docstatus": 1},
        fields=["name"],
        limit=1
    )

    reference_invoice = original_invoice[0]["name"] if original_invoice else None
    if not reference_invoice:
        frappe.log(f"No original Purchase Invoice found with GRN No: {dr_no}")


    # Create Journal Entry
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "voucher_type": "Debit Note",
        "posting_date": posting_date,
        "custom_bill_category": "GRN Return",
        "custom_return_no": dr_return_no,
        "custom_bill_number": dr_no,
        "custom_supplier_name": supplier_n,
        "company": company,
        "user_remark": f"Auto return for GRN {dr_no} - Return {dr_return_no}",
        "accounts": [
            {
                "account": creditor_account,
                "party_type": "Supplier",
                "party": supplier_name,
                "debit_in_account_currency": total_amount,
                "reference_type": "Purchase Invoice",
                "reference_name": reference_invoice,
                "cost_center": None
            },
            {
                "account": stock_account,
                "credit_in_account_currency": total_amount,
                "cost_center": None
            }
        ]
    })

    try:
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.db.commit()
        frappe.log(f"Journal Entry created for Return No: {dr_return_no}, Amount: {total_amount}")
    except Exception as e:
        frappe.log_error(f"Failed to create Journal Entry for {dr_return_no}: {e}")


@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # from_date = 1751341619000  # Fixed from date
        # to_date = 1753328819000    # Fixed to date
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

        return_data = fetch_grn_returns(jwt_token, from_date, to_date)
        frappe.log("GRN Return data fetched successfully.")

        # Group items by drReturnNo
        grouped_returns = group_return_items_by_drReturnNo(return_data.get("jsonResponse", []))
        
        # Create purchase returns for each grouped return
        for dr_return_no, grouped_return in grouped_returns.items():
            create_journal_entry_for_return(grouped_return)

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()