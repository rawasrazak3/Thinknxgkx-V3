import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v3.thinknxg_kx_v3.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "IPD ADDENDUM BILLING"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)

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
headers_token = fetch_api_details(billing_type)


def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

def fetch_ip_billing(jwt_token, from_date, to_date):
    headers_billing = {
        "Content-Type": headers_token["Content-Type"],
        # "clientCode": "METRO_THINKNXG_FI",
        "clientCode": headers_token["clientCode"],
        # "integrationKey": "OP_BILLING",
        "integrationKey": headers_token["integrationKey"],
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch IPD Addendum Billing data: {response.status_code} - {response.text}")

def get_or_create_customer(customer_name,uhid, payer_type=None):
    # Check if the customer already exists
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "custom_uh_id":uhid})
    if existing_customer:
        return existing_customer

    # Determine customer group based on payer_type
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "insurance":
            customer_group = "Insurance"
        elif payer_type == "cash":
            customer_group = "Cash"
        elif payer_type == "credit":
            customer_group = "Credit"
        else:
            customer_group = "Individual"  # default fallback
    else:
        customer_group = "Individual"

    # Create new customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "custom_uh_id": uhid,
        "customer_name": customer_name,
        "customer_group": customer_group,
        "territory": "All Territories"
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()

    return customer.name

def get_or_create_patient(patient_name,gender):
    existing_patient = frappe.db.exists("Patient", {"patient_name": patient_name})
    if existing_patient:
        return existing_patient
    
    customer = frappe.get_doc({
        "doctype": "Patient",
        "first_name": patient_name,
        "sex": gender
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



def create_journal_entry_from_billing(billing_data):
    bill_no = billing_data["bill_no"]
    date = billing_data["g_creation_time"]
    datetimes =  date/1000.0
    dt = datetime.fromtimestamp(datetimes)
    formatted_date = dt.strftime('%Y-%m-%d')
    if frappe.db.exists("Journal Entry", {"custom_bill_no": bill_no,"docstatus": ["!=", 2]}):
        frappe.log(f"Journal Entry with bill_no {bill_no} already exists.")
        return


    customer_name = billing_data["patient_name"]
    payer_name = billing_data["payer_name"]
    patient_name = billing_data["patient_name"]
    gender = billing_data["patient_gender"]
    uhid = billing_data["uhId"]
    payer_type = billing_data["payer_type"]
    customer = get_or_create_customer(customer_name,uhid,payer_type)
    patient = get_or_create_patient(patient_name, gender)
    payer = get_or_create_customer(payer_name,uhid,payer_type)

    # Check if there is an amount in IP ADVANCE mode
    payment_details = billing_data.get("payment_transaction_details", [])
    has_ip_advance = any(payment.get("amount", 0) > 0 and payment.get("payment_mode_code") == "IP ADVANCE" for payment in payment_details)

    
    treating_department_name = billing_data.get("treating_department_name", "Default Dept")
    cost_center = get_or_create_cost_center(treating_department_name)
    
    def get_or_create_item(service_name,service_type,service_code):
        """Check if the item exists; if not, create it."""
        item_code = service_code if service_code else service_name
        existing_item = frappe.db.exists("Item", {"item_code": item_code})
        if existing_item:
            return existing_item
        
        # Check if the item group exists, if not create it
        item_group = frappe.db.get_value("Item Group", {"name": service_type})
        if not item_group:
            item_group_doc = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": service_type,
                "parent_item_group": "Services",  # Ensure this exists in ERPNext
                "is_group": 0
            })
            item_group_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            item_group = service_type  # Assign the newly created group

        # Create a new item if it doesn't exist
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": service_name,
            "item_group": item_group,  # Ensure you have this group in ERPNext
            "stock_uom": "Nos",
            "is_stock_item":0,
            "is_service_item": 1
        })
        item.insert(ignore_permissions=True)
        frappe.db.commit()

        return item.name

    # Ensure items and cost centers exist before adding them to Sales Invoice
    items = []
    # for service in billing_data.get("item_details", []):
    #     cost_center = get_or_create_cost_center(service["department"], service["subDepartment"])
    #     item_code = get_or_create_item(service["serviceName"],service["serviceType"],service["serviceCode"])  # Ensure item exists

    #     items.append({
    #         "item_code": item_code,
    #         "qty": 1,
    #         "rate": service["service_selling_amount"],
    #         "amount": service["service_selling_amount"],
    #         "cost_center": cost_center
    #     })

    first_service = billing_data.get("item_details", [{}])[0]
    # cost_center = get_or_create_cost_center(
    #     first_service.get("department", "Default Dept"),
    #     first_service.get("subDepartment", "Default SubDept")
    # )
    get_or_create_cost_center(treating_department_name)

    # item_rate = billing_data["selling_amount"]
    # items = [{
    #     "item_code": "Journal Item",  # Or a predefined item code
    #     "qty": 1,
    #     "rate": item_rate,
    #     "amount": item_rate,
    #     "cost_center": cost_center
    # }]
    discount_amount = billing_data["selling_amount"] - billing_data["total_amount"]
    tax_amount = billing_data["tax"]


    # Tax table entry
    # taxes = [{
    #     "charge_type": "Actual",
    #     "account_head": "Output VAT 5% - AN" if tax_amount > 0 else "Output VAT Zero - AN",  # Change to your tax account
    #     # "rate": 0 if tax_amount == 0 else (tax_amount / billing_data["total_amount"]) * 100,
    #     "tax_amount": 0 if tax_amount == 0 else tax_amount,
    #     "description": "Output VAT 5% - AN" if tax_amount > 0 else "Output VAT zero - AN"
    # }]

    
    
    # je = frappe.get_doc({
    #     "doctype": "Journal Entry",
    #     "customer": customer,
    #     "custom_payer": payer,
    #     "patient": patient,
    #     "custom_bill": "IP Billing",
    #     "set_posting_time":1,
    #     "posting_date": formatted_date,
    #     "due_date": formatted_date,
    #     "custom_bill_no": bill_no,
    #     "custom_uh_id": billing_data["uhId"],
    #     "custom_admission_id_": billing_data["admissionId"],
    #     "custom_admission_type": billing_data["admissionType"],
    #     "items": items,
    #     "discount_amount": discount_amount,
    #     "total": billing_data["selling_amount"],
    #     "grand_total": billing_data["selling_amount"] + tax_amount,        
    #     "disable_rounded_total":1,
    #     "taxes": taxes,
    #     "cost_center":cost_center,
    #     "allocate_advances_automatically": 1 if has_ip_advance else 0
    # })

    # 🔵 BUILD ACCOUNTS TABLE FOR JOURNAL ENTRY

    accounts = []

    # Debit: Cash / Bank / Debtors
    accounts.append({
        "account": "Debtors - AN",   #  change if Cash billing
        "party_type": "Customer",
        "party": customer,
        "debit_in_account_currency": billing_data["selling_amount"] + tax_amount,
        "credit_in_account_currency": 0,
        "cost_center": cost_center
    })

    # Credit: IPD Income
    accounts.append({
        "account": "Sales - AN",   # CONFIRM THIS ACCOUNT EXISTS
        "debit_in_account_currency": 0,
        "credit_in_account_currency": billing_data["selling_amount"],
        "cost_center": cost_center,
        "party_type": "customer",
        "party": customer
        
    })

    # Credit VAT if applicable
    if tax_amount > 0:
        accounts.append({
            "account": "Output VAT 5% - AN",
            "debit_in_account_currency": 0,
            "credit_in_account_currency": tax_amount,
            "cost_center": cost_center
        })


    je = frappe.get_doc({
    "doctype": "Journal Entry",
    "voucher_type": "Journal Entry",
    "posting_date": formatted_date,
    "set_posting_time": 1,

    "custom_bill_category": "IPD ADDENDUM",
    "custom_bill_no": bill_no,
    "custom_uh_id": billing_data["uhId"],
    "custom_admission_id_": billing_data["admissionId"],
    "custom_admission_type": billing_data["admissionType"],

    # THIS IS THE MOST IMPORTANT LINE
    "accounts": accounts
})

    
    try:
        frappe.get_doc(je).insert(ignore_permissions=True)
        frappe.db.commit()
        je.submit()
        create_journal_entry(je.name, billing_data)
        frappe.log(f"Journal Entry created successfully with bill_no: {bill_no}")
        # create_uepr_journal_entry(sales_invoice.name, billing_data)
        # create_payment_entry(sales_invoice.name, customer, billing_data)
        

    except Exception as e:
        frappe.log_error(f"Failed to create JE: {e}")
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
        print("---f", from_date)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
        print("----t", to_date)
        billing_data = fetch_ip_billing(jwt_token, from_date, to_date)
        frappe.log("IPD Addedndum Billing data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            print("creating journal entry")
            create_journal_entry_from_billing(billing["ipd_addendum_billing"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

def safe_insert_journal_entry(doc):
    # Check if a Journal Entry with same user_remark and company exists
    existing = frappe.get_all(
        "Journal Entry",
        filters={
            "user_remark": doc.user_remark,
            "company": doc.company
        },
        limit=1
    )
    if existing:
        return frappe.get_doc("Journal Entry", existing[0].name)
    return doc.insert(ignore_permissions=True)

def create_journal_entry(reference_name, billing_data):
    payment_details = billing_data.get("payment_transaction_details", [])
    customer_name = billing_data["payer_name"]
    patient_name = billing_data["patient_name"]
    uhid = billing_data["uhId"]

    authorized_amount = billing_data.get("authorized_amount", 0)
    payer_amounts = billing_data.get("received_amount", 0)
    payer_amount = authorized_amount + payer_amounts

    journal_entry = frappe.get_doc("Journal Entry", reference_name)
    custom_uh_id = journal_entry.get("custom_uh_id")
    bill_no = journal_entry.get("custom_bill_no")
    item_cost_center = journal_entry.items[0].cost_center

    date = billing_data["g_creation_time"]
    datetimes = date / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    formatted_date = dt.strftime('%Y-%m-%d')

    
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company)

    cash_account = company_doc.default_cash_account
    bank_account = company_doc.default_bank_account
    
    # Initialize journal entry rows
    je_entries = []
    je_entries.append({
            "account": "Debtors - AN",
            "party_type": "Customer",
            "party": patient_name,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": payer_amount,
            "reference_type": "Journal Entry",
            "reference_name":reference_name,
            "cost_center":item_cost_center
        })
    # Handling Credit Payment Mode
    credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
    if authorized_amount>0:
        je_entries.append({
            "account": "Debtors - AN",  # Replace with actual debtors account
            "party_type": "Customer",
            "party": customer_name,
            "debit_in_account_currency": authorized_amount,
            "credit_in_account_currency": 0,
        })
        

    # Handling Cash Payment Mode
    for payment in payment_details:
        if payment["payment_mode_code"].lower() == "cash":
            je_entries.append({
                "account": cash_account,  # Replace with actual cash account
                "debit_in_account_currency": payment["amount"],
                "credit_in_account_currency": 0,
                # "reference_type": "Sales Invoice",
                # "reference_name":sales_invoice_name
            })

    # Handling Other Payment Modes (UPI, Card, etc.)
    bank_payment_total = sum(
        p["amount"] for p in payment_details if p["payment_mode_code"] not in ["cash", "credit","IP ADVANCE"]
    )
    if bank_payment_total > 0:
        je_entries.append({
            "account": bank_account,  # Replace with actual bank account
            "debit_in_account_currency": bank_payment_total,
            "credit_in_account_currency": 0,
            # "reference_type": "Sales Invoice",
            # "reference_name":sales_invoice_name
        })

    # Create Journal Entry if there are valid transactions
    if je_entries:
        je_doc = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "accounts": je_entries,
            "custom_bill_category": "IPD ADDENDUM",   # Set from Sales Invoice
            "custom_uh_id": custom_uh_id, 
            "custom_bill_number": bill_no, 
            "user_remark": f"Journal Entry: {reference_name}, Patient: {patient_name} (UHID: {uhid})"
        })
        je_doc = safe_insert_journal_entry(je_doc)
        # je_doc.insert(ignore_permissions=True)
        # frappe.db.commit()
        # je_doc.submit()
        if je_doc.docstatus != 1:
            je_doc.submit()

        frappe.db.commit()

        # Link Journal Entry to Sales Invoice
        # frappe.db.set_value("Sales Invoice", sales_invoice_name, "journal_entry", je_doc.name)
        frappe.msgprint(f"Journal Entry {je_doc.name} created successfully.")

def create_uepr_journal_entry(reference_name, billing_data):

    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in billing_data.get("item_details", [])
    )
    if not total_uepr:
        frappe.log(f"No ueprValue present for {reference_name}; JE not created.")
        return

    sinv = frappe.get_doc("Jounal Entry", reference_name)
    posting_date = sinv.posting_date
    cost_center = sinv.items[0].cost_center
    custom_uh_id = sinv.custom_uh_id

    je_doc = frappe.get_doc({
        "doctype": "Journal Entry",
        "posting_date": posting_date,
        "custom_bill_category": "IPD ADDENDUM",
        "custom_uh_id": custom_uh_id,
        "custom_reference_name" : reference_name,
        "accounts": [
            { 
                "account": "Cost of Goods Sold - AN",
                "debit_in_account_currency": total_uepr,
                "credit_in_account_currency": 0,
                # "reference_type": "Sales Invoice",
                # "reference_name": sales_invoice_name,
                "cost_center": cost_center
            },
            {
                "account": "Stock In Hand - AN",
                "debit_in_account_currency": 0,
                "credit_in_account_currency": total_uepr,
                # "reference_type": "Sales Invoice",
                # "reference_name": sales_invoice_name,
                "cost_center": cost_center
            }
        ],
        "user_remark": f"UEPR value booking for {reference_name}"
    })
    je_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    je_doc.submit()
    frappe.msgprint(f"UEPR Journal Entry {je_doc.name} created (amount {total_uepr}).")