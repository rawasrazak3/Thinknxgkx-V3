

frappe.ui.form.on("Payment Entry", {
    references_on_form_rendered(frm) {

        frm.doc.references.forEach(row => {
            if (row.reference_doctype === "Journal Entry" && row.reference_name) {

                frappe.db.get_doc("Journal Entry", row.reference_name).then(doc => {
                    frappe.model.set_value(row.doctype, row.name, "custom_bill_number", doc.custom_bill_number);
                    frappe.model.set_value(row.doctype, row.name, "custom_grn_number", doc.custom_grn_number);
                    frappe.model.set_value(row.doctype, row.name, "posting_date", doc.posting_date);
                });
            }
        });

        // Refresh table to show values
        frm.fields_dict.references.grid.refresh();
    }
});

