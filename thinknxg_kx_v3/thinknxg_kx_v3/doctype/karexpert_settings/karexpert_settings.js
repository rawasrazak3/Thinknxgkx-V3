// Copyright (c) 2025, Thinknxg and contributors
// For license information, please see license.txt

frappe.ui.form.on("Karexpert  Table", {
	execute: function(frm, cdt, cdn) {
		console.log("Button clicked");
		let row = locals[cdt][cdn];

		let method_map = {
			"OP BILLING": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.create_sales_invoice.main",
				message: "OP Sales Invoice Created"
			},
			"IPD BILLING": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.create_sinv_ip.main",
				message: "IP Sales Invoice Created"
			},
			"DUE SETTLEMENT": {
				method:"thinknxg_kx_v3.thinknxg_kx_v3.custom_script.due_settlement.main",
				message: "Due settlement Created"
			},
			"ADVANCE DEPOSIT": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.advance_deposit.main",
				message: "Advance Deposit Created"
			},
			"ADVANCE DEPOSIT REFUND": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.advance_deposit_refund.main",
				message: "Advance Deposit Refund Created"
			},
			"OP PHARMACY BILLING": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.op_pharmacy_bill.main",
				message: "OP pharmacy Sales Invoice Created"
			},
			"GRN CREATION SUMMARY": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.grn_creation.main",
				message: "Purchase  Invoice Created"
			},
			"OP BILLING REFUND": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.op_refund.main",
				message: "OP sales return  Invoice Created"
			},
			"PHARMACY BILLING REFUND": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.pharmacy_billing_refund.main",
				message: "Pharmacy sales return  Invoice Created"
			},
			"GRN RETURN DETAIL": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.grn_return.main",
				message: "Purchase Invoice return Created"
			},
			"IPD ADDENDUM BILLING": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.ipd_addendum.main",
				message: "IPD Addendum Invoice Created"
			},
			"AR BILL SETTLEMENT": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.ar_bill_settlement.main",
				message: "AR Settlement Bill Created"
			},
			"DOCTOR PAYOUT": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.doctor_payout.main",
				message: "Doctor Payout Created"
			},
			"GET MAIN STORE CONSUMPTION": {
				method:"thinknxg_kx_v3.thinknxg_kx_v3.custom_script.stock_consumption.main",
				message: "Stock Consumption Created"
			},
			"SUPPLIER CREATION": {
				method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.supplier_creation.main",
				message: "Suppliers Created"
			}
		};

		let billing_info = method_map[row.billing_type];

		if (!billing_info) {
            frappe.msgprint("Unsupported billing type selected.");
            return;
        }

        frappe.confirm(
            "Are you sure you want to execute this action?",
            function() {
                // YES clicked
                frappe.call({
                    method: billing_info.method,
                    args: { row_data: row },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(billing_info.message);
                        } else {
                            frappe.msgprint("An error occurred while creating the document.");
                        }
                    }
                });
            },
            function() {
                // NO clicked
                frappe.msgprint("Execution cancelled.");
            }
        );
    }
});


frappe.ui.form.on("Karexpert Settings", {
    refresh: function(frm) {
        frm.add_custom_button("Execute Selected", function() {
            let selected_rows = (frm.doc.table_cbzy || []).filter(r => r.is_selected);

            if (!selected_rows.length) {
                frappe.msgprint("Please select at least one row to execute.");
                return;
            }

            frappe.confirm(
                `Are you sure you want to execute ${selected_rows.length} actions?`,
                function() {
                    console.log("clicked---");

                    let method_map = {
						"OP BILLING": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.create_sales_invoice.main",
							message: "OP Sales Invoice Created"
						},
						"IPD BILLING": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.create_sinv_ip.main",
							message: "IP Sales Invoice Created"
						},
						"DUE SETTLEMENT": {
							method:"thinknxg_kx_v3.thinknxg_kx_v3.custom_script.due_settlement.main",
							message: "Due settlement Created"
						},
						"ADVANCE DEPOSIT": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.advance_deposit.main",
							message: "Advance Deposit Created"
						},
						"ADVANCE DEPOSIT REFUND": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.advance_deposit_refund.main",
							message: "Advance Deposit Refund Created"
						},
						"OP PHARMACY BILLING": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3custom_script.pharmacy_bill.main",
							message: "OP pharmacy Sales Invoice Created"
						},
						"GRN CREATION SUMMARY": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.grn_creation.main",
							message: "Purchase  Invoice Created"
						},
						"OP BILLING REFUND": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.op_refund.main",
							message: "OP sales return  Invoice Created"
						},
						"PHARMACY BILLING REFUND": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.pharmacy_refund.main",
							message: "Pharmacy sales return  Invoice Created"
						},
						"GRN RETURN DETAIL": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.grn_return.main",
							message: "Purchase Invoice return Created"
						},
						"IPD ADDENDUM BILLING": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.ipd_addendum.main",
							message: "IPD Addendum Invoice Created"
						},
						"AR BILL SETTLEMENT": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.ar_bill_settlement.main",
							message: "AR Settlement Bill Created"
						},
						"DOCTOR PAYOUT": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.doctor_payout.main",
							message: "Doctor Payout Created"
						},
						"GET MAIN STORE CONSUMPTION": {
							method:"thinknxg_kx_v3.thinknxg_kx_v3.custom_script.stock_consumption.main",
							message: "Stock Consumption Created"
						},
						"SUPPLIER CREATION": {
							method: "thinknxg_kx_v3.thinknxg_kx_v3.custom_script.supplier_creation.main",
							message: "Suppliers Created"
						}
                    };

                    function execute_row(row) {
                        let billing_info = method_map[row.billing_type];
                        if (!billing_info) {
                            frappe.msgprint(`Unsupported billing type for row ${row.name}`);
                            return;
                        }

                        frappe.call({
                            method: billing_info.method,
                            args: { row_data: row },
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint(billing_info.message);
                                } else {
                                    frappe.msgprint(`Error in row ${row.name}`);
                                }
                            }
                        });
                    }

                    // Separate advance deposit from others
                    let advance_rows = selected_rows.filter(r => r.billing_type === "ADVANCE DEPOSIT");
                    let other_rows = selected_rows.filter(r => r.billing_type !== "ADVANCE DEPOSIT");

                    if (advance_rows.length) {
                        advance_rows.forEach(row => execute_row(row));

                        setTimeout(() => {
                            other_rows.forEach(row => execute_row(row));
                        }, 30000); // 30s delay
                    } else {
                        other_rows.forEach(row => execute_row(row));
                    }
                }
            );
        });
    }
});

frappe.ui.form.on("Karexpert Settings", {
    refresh(frm) {
        $("button:contains('Select All')").off('click').on('click', () => {
            (frm.doc.table_cbzy || []).forEach(row => {
                row.is_selected = 1;
            });
            frm.refresh_field("table_cbzy");
        });

        $("button:contains('Unselect All')").off('click').on('click', () => {
            (frm.doc.table_cbzy || []).forEach(row => {
                row.is_selected = 0;
            });
            frm.refresh_field("table_cbzy");
        });
    }
});