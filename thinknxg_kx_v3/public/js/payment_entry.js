
// frappe.ui.form.on("Payment Entry", {
//     references_on_form_rendered(frm) {

//         frm.doc.references.forEach(row => {
//             if (row.reference_doctype === "Journal Entry" && row.reference_name) {

//                 frappe.db.get_doc("Journal Entry", row.reference_name).then(doc => {
//                     frappe.model.set_value(row.doctype, row.name, "custom_bill_number", doc.custom_bill_number);
//                     frappe.model.set_value(row.doctype, row.name, "custom_grn_number", doc.custom_grn_number);
//                     frappe.model.set_value(row.doctype, row.name, "posting_date", doc.posting_date);
//                 });
//             }
//         });

//         // Refresh table to show values
//         frm.fields_dict.references.grid.refresh();
//     }
// });


// frappe.ui.form.on('Payment Entry', {
//     refresh(frm) {

//         // Ensure references grid exists
//         if (!frm.fields_dict.references) return;

//         // Remove old handlers to avoid duplicate firing
//         frm.fields_dict.references.grid.wrapper
//             .off('click.allocate_row')

//             // Attach click handler to grid rows
//             .on('click.allocate_row', '.grid-row', function () {

//                 let idx = $(this).attr('data-idx');
//                 if (!idx) return;

//                 // Find the clicked row
//                 let row = frm.doc.references.find(r => r.idx == idx);
//                 if (!row) return;

//                 let paid_amount = flt(frm.doc.paid_amount || 0);

//                 // Calculate total allocated so far
//                 let total_allocated = frm.doc.references.reduce(
//                     (sum, r) => sum + flt(r.allocated_amount),
//                     0
//                 );

//                 let remaining = paid_amount - total_allocated;

//                 // Stop if nothing left to allocate
//                 if (remaining <= 0) {
//                     frappe.msgprint(__('Paid Amount fully allocated'));
//                     return;
//                 }

//                 // Allocate min(outstanding, remaining)
//                 let allocation = Math.min(
//                     flt(row.outstanding_amount),
//                     remaining
//                 );

//                 //use frappe.model.set_value
//                 frappe.model.set_value(
//                     row.doctype,
//                     row.name,
//                     'allocated_amount',
//                     allocation
//                 );
//             });
//     }
// });

frappe.ui.form.on("Payment Entry", {
    references_on_form_rendered(frm) {
        if (!frm.doc.references) return;

        frm.doc.references.forEach(row => {
            if (
                row.reference_doctype === "Journal Entry" &&
                row.reference_name &&
                !row.custom_bill_number // prevent refetch
            ) {
                frappe.db.get_value(
                    "Journal Entry",
                    row.reference_name,
                    ["custom_bill_number", "custom_grn_number", "posting_date"]
                ).then(r => {
                    if (r.message) {
                        frappe.model.set_value(row.doctype, row.name, {
                            custom_bill_number: r.message.custom_bill_number,
                            custom_grn_number: r.message.custom_grn_number,
                            posting_date: r.message.posting_date
                        });
                    }
                });
            }
        });
    },

    refresh(frm) {
        if (!frm.fields_dict.references) return;

        frm.fields_dict.references.grid.wrapper
            .off("click.allocate_row")
            .on("click.allocate_row", ".grid-row", function () {

                let idx = $(this).attr("data-idx");
                if (!idx) return;

                let row = frm.doc.references.find(r => r.idx == idx);
                if (!row) return;

                let paid_amount = flt(frm.doc.paid_amount || 0);

                // Exclude current row from allocated sum
                let total_allocated = frm.doc.references.reduce(
                    (sum, r) =>
                        r.name === row.name
                            ? sum
                            : sum + flt(r.allocated_amount),
                    0
                );

                let remaining = paid_amount - total_allocated;

                if (remaining <= 0) {
                    frappe.msgprint(__("Paid Amount fully allocated"));
                    return;
                }

                let allocation = Math.min(
                    flt(row.outstanding_amount),
                    remaining
                );

                frappe.model.set_value(
                    row.doctype,
                    row.name,
                    "allocated_amount",
                    allocation
                );
            });
    }
});
