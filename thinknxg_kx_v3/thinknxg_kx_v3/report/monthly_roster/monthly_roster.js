// Copyright (c) 2026, thinknxg and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Roster"] = {
	"filters": [

        {
            "fieldname": "year",
            "label": "Year",
            "fieldtype": "Select",
            "options": ["2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033","2034", "2035"],
            "reqd": 1,
            "default": (new Date()).getFullYear().toString()  // current year
        },
        {
            "fieldname": "month",
            "label": "Month",
            "fieldtype": "Select",
             "options": [
				"January",
				"February",
				"March",
				"April",
				"May",
				"June",
				"July",
				"August",
				"September",
				"October",
				"November",
				"December"
			],
            "reqd": 1,
            "default": function() {
                const monthNames = [
                    "January","February","March","April","May","June",
                    "July","August","September","October","November","December"
                ];
                const today = new Date();
                return monthNames[today.getMonth()];  // getMonth() returns 0–11
            }()
        },
		 {
            "fieldname": "company",
            "label": "Company",
            "fieldtype": "Link",
            "options": "Company",
			"reqd": 1,
            "default": frappe.defaults.get_user_default("Company")  // default company
        },
        {
            "fieldname": "department",
            "label": "Department",
            "fieldtype": "Link",
            "options": "Department"
        }
    ]
};