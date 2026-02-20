
console.log("Custom Leave Application override loaded");

frappe.ui.form.on("Leave Application", {
    before_load(frm) {
        const user_type = frappe.boot.user ? frappe.boot.user.user_type : "";

        // Block dashboard initialization for ESS users
        if (user_type === "Employee Self Service") {
            Object.defineProperty(frm, "dashboard", {
                get: function () {
                    return {
                        refresh: function () {},
                        add_section: function () {},
                        show: function () {},
                        wrapper: $("<div></div>"), // dummy placeholder
                    };
                },
                configurable: true,
            });
            console.log("🧱 Dashboard initialization blocked for ESS user");
        }
    },

    async onload(frm) {
        const user_type = frappe.boot.user ? frappe.boot.user.user_type : "";

        // Ensure employee auto-load works for ESS users too
        if (!frm.doc.employee) {
            try {
                const employee = await hrms.get_current_employee(frm);
                if (employee) {
                    frm.set_value("employee", employee);
                    console.log("✅ Employee auto-loaded:", employee);
                }
            } catch (err) {
                console.warn("⚠️ Failed to auto-load employee:", err);
            }
        }

        // Optional: set default posting date if missing
        if (!frm.doc.posting_date) {
            frm.set_value("posting_date", frappe.datetime.get_today());
        }
    },

    refresh(frm) {
        const user_type = frappe.boot.user ? frappe.boot.user.user_type : "";

        //  Apply Leave Type filter (for all users)
        if (frm.doc.employee) {
            frappe.call({
                method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
                async: false,
                args: {
                    employee: frm.doc.employee,
                    date: frm.doc.from_date || frm.doc.posting_date,
                },
                callback: function (r) {
                    if (!r.exc && r.message) {
                        const leave_details = r.message["leave_allocation"] || {};
                        const lwps = r.message["lwps"] || [];
                        const allowed_leave_types = Object.keys(leave_details).concat(lwps);

                        frm.set_query("leave_type", function () {
                            return {
                                filters: [["leave_type_name", "in", allowed_leave_types]],
                            };
                        });

                        console.log("Leave Type filter applied:", allowed_leave_types);
                    }
                },
            });
        }

        //  Confirm dashboard suppression for ESS
        if (user_type === "Employee Self Service") {
            console.log("Dashboard completely disabled for ESS user");
        }
    },

    make_dashboard(frm) {
        const user_type = frappe.boot.user ? frappe.boot.user.user_type : "";
        if (user_type === "Employee Self Service") return;

        // Default dashboard behavior for HR/Admin
        if (!frm.trigger_original_dashboard) {
            frm.trigger_original_dashboard = function () {
                if (frm.doc.employee) {
                    frappe.call({
                        method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
                        async: false,
                        args: {
                            employee: frm.doc.employee,
                            date: frm.doc.from_date || frm.doc.posting_date,
                        },
                        callback: function (r) {
                            if (!r.exc && r.message["leave_allocation"]) {
                                const leave_details = r.message["leave_allocation"];
                                const lwps = r.message["lwps"] || [];

                                $("div.form-dashboard-section.custom").remove();

                                frm.dashboard.add_section(
                                    frappe.render_template("leave_application_dashboard", {
                                        data: leave_details,
                                    }),
                                    __("Allocated Leaves")
                                );

                                frm.dashboard.show();

                                let allowed_leave_types = Object.keys(leave_details).concat(lwps);

                                frm.set_query("leave_type", function () {
                                    return {
                                        filters: [["leave_type_name", "in", allowed_leave_types]],
                                    };
                                });
                            }
                        },
                    });
                }
            };
        }

        frm.trigger_original_dashboard();
    },
});
