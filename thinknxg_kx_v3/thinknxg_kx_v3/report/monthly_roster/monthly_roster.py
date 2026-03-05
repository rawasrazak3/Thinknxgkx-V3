
import frappe
from datetime import datetime, timedelta
import calendar


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_month_number(month_name):
    """Convert month name to month number"""
    return list(calendar.month_name).index(month_name)


def get_columns(filters):
    year = int(filters.get("year"))
    month_name = filters.get("month")

    # Convert month name → number
    month = get_month_number(month_name)

    days = calendar.monthrange(year, month)[1]

    columns = [{
        "label": "Employee",
        "fieldname": "employee",
        "fieldtype": "Data",
        "width": 180
    }]

    for day in range(1, days + 1):
        date_obj = datetime(year, month, day)
        day_name = date_obj.strftime("%a")
        label = f"{day_name} {day:02d}"

        columns.append({
            "label": label,
            "fieldname": f"day_{day}",
            "fieldtype": "HTML",
            "width": 160
        })

    return columns


# def get_data(filters):
#     year = int(filters.get("year"))
#     month_name = filters.get("month")
#     company = filters.get("company")
#     department = filters.get("department")

#     # Convert month name → number
#     month = get_month_number(month_name)

#     first_day = datetime(year, month, 1).date()
#     last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()

#     # Employee filters
#     employee_conditions = {}
#     if department:
#         employee_conditions["department"] = department
#     if company:
#         employee_conditions["company"] = company

#     employee_list = frappe.get_all(
#         "Employee",
#         filters=employee_conditions,
#         fields=["name", "employee_name"]
#     )

#     employee_ids = [e.name for e in employee_list]

#     if not employee_ids:
#         return []

#     assignments = frappe.db.sql("""
#         SELECT
#             sa.employee,
#             e.employee_name,
#             sa.shift_type,
#             sa.start_date,
#             sa.end_date
#         FROM `tabShift Assignment` sa
#         JOIN `tabEmployee` e ON sa.employee = e.name
#         WHERE sa.employee IN %(employee_ids)s
#         AND sa.start_date <= %(last_day)s
#         AND (sa.end_date IS NULL OR sa.end_date >= %(first_day)s)
#         ORDER BY e.employee_name
#     """, {
#         "employee_ids": tuple(employee_ids),
#         "first_day": first_day,
#         "last_day": last_day
#     }, as_dict=1)

#     days_in_month = calendar.monthrange(year, month)[1]
#     employee_map = {}

#     for row in assignments:
#         emp_display = f"{row.employee_name} ({row.employee})"

#         if emp_display not in employee_map:
#             employee_map[emp_display] = {"employee": emp_display}
#             for d in range(1, days_in_month + 1):
#                 employee_map[emp_display][f"day_{d}"] = ""

#         current_date = max(row.start_date, first_day)
#         end_date = row.end_date if row.end_date else last_day

#         while current_date <= min(end_date, last_day):
#             day = current_date.day
#             employee_map[emp_display][f"day_{day}"] = f"<b>{row.shift_type}</b>"
#             current_date += timedelta(days=1)

#     return list(employee_map.values())

def get_data(filters):
    year = int(filters.get("year"))
    month_name = filters.get("month")
    company = filters.get("company")
    department = filters.get("department")

    month = get_month_number(month_name)

    first_day = datetime(year, month, 1).date()
    last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()

    # Employee filters
    employee_conditions = {}
    if department:
        employee_conditions["department"] = department
    if company:
        employee_conditions["company"] = company

    employee_list = frappe.get_all(
        "Employee",
        filters=employee_conditions,
        fields=["name", "employee_name"]
    )

    employee_ids = [e.name for e in employee_list]

    if not employee_ids:
        return []

    # Fetch Shift Assignments
    assignments = frappe.db.sql("""
		SELECT
			sa.employee,
			e.employee_name,
			sa.shift_type,
			sa.start_date,
			sa.end_date,
			st.custom_break_start_time,
			st.custom_break_end_time
		FROM `tabShift Assignment` sa
		JOIN `tabEmployee` e ON sa.employee = e.name
		LEFT JOIN `tabShift Type` st ON sa.shift_type = st.name
		WHERE sa.docstatus = 1
		AND sa.employee IN %(employee_ids)s
		AND sa.start_date <= %(last_day)s
		AND (sa.end_date IS NULL OR sa.end_date >= %(first_day)s)
	""", {
		"employee_ids": tuple(employee_ids),
		"first_day": first_day,
		"last_day": last_day
	}, as_dict=1)

    # Fetch Approved Leave
    leaves = frappe.db.sql("""
        SELECT employee, from_date, to_date
        FROM `tabLeave Application`
        WHERE docstatus = 1
        AND status = 'Approved'
        AND employee IN %(employee_ids)s
        AND from_date <= %(last_day)s
        AND to_date >= %(first_day)s
    """, {
        "employee_ids": tuple(employee_ids),
        "first_day": first_day,
        "last_day": last_day
    }, as_dict=1)

    # Fetch Holidays
    holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")

    holidays = frappe.db.sql("""
        SELECT holiday_date, description, weekly_off
        FROM `tabHoliday`
        WHERE parent = %s
        AND holiday_date BETWEEN %s AND %s
    """, (holiday_list, first_day, last_day), as_dict=1)

    holiday_map = {h.holiday_date: h for h in holidays}

    days_in_month = calendar.monthrange(year, month)[1]
    employee_map = {}

    # Initialize all employees first
    for emp in employee_list:
        emp_display = f"{emp.employee_name} ({emp.name})"
        employee_map[emp_display] = {"employee": emp_display}

        for d in range(1, days_in_month + 1):
            date_obj = datetime(year, month, d).date()

            # Holiday / Weekly Off
            if date_obj in holiday_map:
                if holiday_map[date_obj].weekly_off:
                    employee_map[emp_display][f"day_{d}"] = (
                        "<span style='color:blue; font-weight:bold;'>WO</span>"
                    )
                else:
                    employee_map[emp_display][f"day_{d}"] = (
                        f"<span style='color:purple;'>{holiday_map[date_obj].description}</span>"
                    )

            # Leave
            elif any(
                leave.employee == emp.name and
                leave.from_date <= date_obj <= leave.to_date
                for leave in leaves
            ):
                employee_map[emp_display][f"day_{d}"] = (
                    "<span style='color:green; font-weight:bold;'>L</span>"
                )

            # Default NA
            else:
                employee_map[emp_display][f"day_{d}"] = (
                    "<span style='color:red; font-weight:bold;'>NA</span>"
                )

    # Apply Shift Assignments (Only override NA)
    for row in assignments:
        emp_display = f"{row.employee_name} ({row.employee})"

        current_date = max(row.start_date, first_day)
        end_date = row.end_date if row.end_date else last_day

        while current_date <= min(end_date, last_day):
            day = current_date.day

            # Only replace if current value is NA
            if "NA" in employee_map[emp_display][f"day_{day}"]:
                employee_map[emp_display][f"day_{day}"] = (
                    f"<b>{row.shift_type}</b>"
                )

            current_date += timedelta(days=1)

    return list(employee_map.values())