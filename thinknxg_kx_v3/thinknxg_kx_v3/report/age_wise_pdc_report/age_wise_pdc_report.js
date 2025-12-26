// Copyright (c) 2025, thinknxg and contributors
// For license information, please see license.txt


frappe.query_reports["Age-wise PDC Report"] = {
    "filters": [
		{
            "fieldname": "party_type",
            "label": __("Party Type"),
            "fieldtype": "Select",
            "options": ["Customer", "Supplier"],
            "default": "Customer",
            "reqd": 1,  // Required filter
            "on_change": function() {
                let party_type = frappe.query_report.get_filter_value('party_type');
                
                // Dynamically change the party filter based on the selected party_type
                frappe.query_report.set_filter_value('party', '');  // Clear the current party selection
                if (party_type === "Customer") {
                    frappe.query_report.get_filter('party').df.options = "Customer";
                } else if (party_type === "Supplier") {
                    frappe.query_report.get_filter('party').df.options = "Supplier";
                }

                // Force a full report refresh after setting the new filter options
                frappe.query_report.refresh();  // This triggers the report data to refresh
            }
        },
        {
            "fieldname": "party",
            "label": __("Party "),
            "fieldtype": "Link",
            "options": "Customer", // Can also be "Supplier" if needed
            "default": "",
            "reqd": 0
        },
        // {
        //     "fieldname": "party",
        //     "label": __("Party "),
        //     "fieldtype": "Link",
        //     "options": "Supplier", // Can also be "Supplier" if needed
        //     "default": "",
        //     "reqd": 0
        // },
        {
            "fieldname": "payment_type",
            "label": __("Payment Type"),
            "fieldtype": "Select",
            "options": ["Receive", "Pay", "Internal Transfer"],
            "default": "Receive",
            "reqd": 0  // Optional filter, not required
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate(),  
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.nowdate(), 30), // Default to 30 days after today
            "reqd": 1
        }
    ],

    "onload": function(report) {
        // This will trigger when the report is loaded
        frappe.query_report.refresh();
        console.log("Report Loaded: Age Wise PDC Report");

        // You can add custom JS actions on report load here
    },

    "formatter": function(value, row, column, data, default_formatter) {
        // Custom formatter for fields if needed
        if (column.fieldname === "amount" && value) {
            // Format amount as currency, add a specific style, etc.
            value = `<span style="color:green;">${value}</span>`;
        }
        return default_formatter(value, row, column, data);
    },
    "before_load": function() {
    frappe.query_report.refresh();
    },
    
    "formatter": function(value, row, column, data, default_formatter) {
    console.log("Data row:", row, "Column:", column, "Value:", value);  // Log data for debugging
    return default_formatter(value, row, column, data);
    }


};