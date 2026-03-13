
import frappe

def execute():
    jes = frappe.get_all("Journal Entry", pluck="name")

    for je in jes:
        doc = frappe.get_doc("Journal Entry", je)

        for idx, row in enumerate(doc.accounts, start=1):
            if row.account and not row.bank_account:
                # Get the bank account name from Bank Account doctype
                bank_name = frappe.db.get_value(
                    "Bank Account",
                    {"account": row.account},
                    "account_name"
                )

                if bank_name:
                    # Directly update the child table row in the database
                    frappe.db.set_value(
                        "Journal Entry Account",  # Child table
                        row.name,                # row primary key
                        "bank_account",          # field to update
                        bank_name,
                        update_modified=True     # update modified timestamp
                    )
                    print(f"Updated JE: {doc.name}, Row #{idx} with Bank Account: {bank_name}")

    frappe.db.commit()