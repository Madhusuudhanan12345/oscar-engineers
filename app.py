import os
import sqlite3

from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from dotenv import load_dotenv

from werkzeug.security import check_password_hash


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
SECRET_KEY = os.getenv("SECRET_KEY")


# =========================================================
# SECURITY CHECK
# =========================================================

if not ADMIN_USERNAME:
    raise RuntimeError(
        "ADMIN_USERNAME is missing. Please add it to .env"
    )

if not ADMIN_PASSWORD_HASH:
    raise RuntimeError(
        "ADMIN_PASSWORD_HASH is missing. Please add it to .env"
    )

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Please add it to .env"
    )


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY


# =========================================================
# DATABASE
# =========================================================

DATABASE = "database.db"


def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_db_connection()


    # =====================================================
    # BOOKINGS
    # =====================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            booking_id TEXT UNIQUE,

            customer_name TEXT NOT NULL,

            mobile TEXT NOT NULL,

            address TEXT NOT NULL,

            ac_brand TEXT,

            ac_type TEXT,

            service_type TEXT,

            preferred_date TEXT,

            preferred_time TEXT,

            problem TEXT,

            status TEXT DEFAULT 'New',

            technician_id INTEGER,

            created_at TEXT
        )
    """)


    # =====================================================
    # TECHNICIANS
    # =====================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS technicians (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            mobile TEXT NOT NULL,

            specialization TEXT,

            username TEXT UNIQUE,

            password TEXT,

            status TEXT DEFAULT 'Active',

            created_at TEXT
        )
    """)


    # =====================================================
    # CUSTOMERS
    # =====================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            mobile TEXT NOT NULL,

            email TEXT,

            address TEXT,

            username TEXT UNIQUE,

            password TEXT,

            status TEXT DEFAULT 'Active',

            created_at TEXT
        )
    """)


    # =====================================================
    # CONTACT MESSAGES
    # =====================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            mobile TEXT,

            email TEXT,

            subject TEXT,

            message TEXT,

            status TEXT DEFAULT 'New',

            created_at TEXT
        )
    """)


    conn.commit()

    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# =========================================================
# LOGIN PORTAL
# =========================================================

@app.route("/login")
def login():

    return render_template(
        "login.html"
    )


# =========================================================
# HIDDEN ADMIN LOGIN
# =========================================================

@app.route(
    "/oscar-control-2026",
    methods=["GET", "POST"]
)
def admin_login():

    error = None


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        # =================================================
        # SECURE ADMIN LOGIN
        # =================================================

        if (
            username == ADMIN_USERNAME
            and check_password_hash(
                ADMIN_PASSWORD_HASH,
                password
            )
        ):

            session.clear()

            session["username"] = ADMIN_USERNAME

            session["name"] = "Oscar Admin"

            session["role"] = "Admin"

            return redirect(
                url_for("dashboard")
            )


        error = (
            "Invalid Admin username or password."
        )


    return render_template(
        "admin_login.html",
        error=error
    )


# =========================================================
# CUSTOMER LOGIN
# =========================================================

@app.route(
    "/customer-login",
    methods=["GET", "POST"]
)
def customer_login():

    error = None

    registered = request.args.get(
        "registered"
    )


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        conn = get_db_connection()


        customer = conn.execute("""
            SELECT *
            FROM customers
            WHERE username = ?
            AND password = ?
            AND status = 'Active'
        """, (
            username,
            password
        )).fetchone()


        conn.close()


        if customer:

            session.clear()

            session["username"] = customer["username"]

            session["name"] = customer["name"]

            session["role"] = "Customer"

            session["customer_id"] = customer["id"]


            return redirect(
                url_for(
                    "customer_dashboard"
                )
            )


        error = (
            "Invalid Customer username or password."
        )


    return render_template(
        "customer_login.html",
        error=error,
        registered=registered
    )


# =========================================================
# CUSTOMER SIGNUP
# =========================================================

@app.route(
    "/customer-signup",
    methods=["GET", "POST"]
)
def customer_signup():

    error = None


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if (
            not name
            or not mobile
            or not username
            or not password
        ):

            error = (
                "Please fill all required fields."
            )


        elif len(password) < 6:

            error = (
                "Password must contain at least 6 characters."
            )


        elif password != confirm_password:

            error = (
                "Passwords do not match."
            )


        else:

            conn = get_db_connection()


            existing = conn.execute("""
                SELECT id
                FROM customers
                WHERE username = ?
            """, (
                username,
            )).fetchone()


            if existing:

                conn.close()

                error = (
                    "Username already exists."
                )


            else:

                conn.execute("""
                    INSERT INTO customers
                    (
                        name,
                        mobile,
                        email,
                        address,
                        username,
                        password,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    mobile,
                    email,
                    address,
                    username,
                    password,
                    "Active",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))


                conn.commit()

                conn.close()


                return redirect(
                    url_for(
                        "customer_login",
                        registered="1"
                    )
                )


    return render_template(
        "customer_signup.html",
        error=error
    )


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

@app.route("/customer-dashboard")
def customer_dashboard():

    if session.get("role") != "Customer":

        return redirect(
            url_for("customer_login")
        )


    return render_template(
        "customer_dashboard.html",
        name=session.get("name")
    )


# =========================================================
# CUSTOMER SERVICES
# =========================================================

@app.route("/my-services")
def my_services():

    if session.get("role") != "Customer":

        return redirect(
            url_for("customer_login")
        )


    customer_id = session.get(
        "customer_id"
    )


    conn = get_db_connection()


    customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE id = ?
    """, (
        customer_id,
    )).fetchone()


    if customer is None:

        conn.close()

        session.clear()

        return redirect(
            url_for("customer_login")
        )


    bookings = conn.execute("""
        SELECT

            bookings.*,

            technicians.name
                AS technician_name,

            technicians.mobile
                AS technician_mobile,

            technicians.specialization
                AS technician_specialization

        FROM bookings

        LEFT JOIN technicians

        ON bookings.technician_id =
           technicians.id

        WHERE bookings.mobile = ?

        ORDER BY bookings.id DESC

    """, (
        customer["mobile"],
    )).fetchall()


    conn.close()


    return render_template(
        "my_services.html",

        name=customer["name"],

        bookings=bookings
    )


# =========================================================
# CUSTOMER PROFILE
# =========================================================

@app.route("/customer-profile")
def customer_profile():

    if session.get("role") != "Customer":

        return redirect(
            url_for("customer_login")
        )


    customer_id = session.get(
        "customer_id"
    )


    conn = get_db_connection()


    customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE id = ?
    """, (
        customer_id,
    )).fetchone()


    conn.close()


    if customer is None:

        return redirect(
            url_for("customer_login")
        )


    return render_template(
        "customer_profile.html",
        customer=customer
    )


# =========================================================
# TECHNICIAN LOGIN
# =========================================================

@app.route(
    "/technician-login",
    methods=["GET", "POST"]
)
def technician_login():

    error = None


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        conn = get_db_connection()


        technician = conn.execute("""
            SELECT *
            FROM technicians
            WHERE username = ?
            AND password = ?
            AND status = 'Active'
        """, (
            username,
            password
        )).fetchone()


        conn.close()


        if technician:

            session.clear()

            session["username"] = (
                technician["username"]
            )

            session["name"] = (
                technician["name"]
            )

            session["role"] = "Technician"

            session["technician_id"] = (
                technician["id"]
            )


            return redirect(
                url_for(
                    "technician_jobs"
                )
            )


        error = (
            "Invalid Technician username or password."
        )


    return render_template(
        "technician_login.html",
        error=error
    )


# =========================================================
# TECHNICIAN JOBS
# =========================================================

@app.route("/technician-jobs")
def technician_jobs():

    if session.get("role") != "Technician":

        return redirect(
            url_for("technician_login")
        )


    technician_id = session.get(
        "technician_id"
    )


    conn = get_db_connection()


    bookings = conn.execute("""
        SELECT *
        FROM bookings
        WHERE technician_id = ?
        ORDER BY id DESC
    """, (
        technician_id,
    )).fetchall()


    conn.close()


    return render_template(
        "technician_jobs.html",

        name=session.get("name"),

        bookings=bookings
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if session.get("role") != "Admin":

        return redirect(
            url_for("admin_login")
        )


    conn = get_db_connection()


    # =====================================================
    # BOOKINGS
    # =====================================================

    bookings = conn.execute("""
        SELECT

            bookings.*,

            technicians.name
                AS technician_name,

            technicians.mobile
                AS technician_mobile

        FROM bookings

        LEFT JOIN technicians

        ON bookings.technician_id =
           technicians.id

        ORDER BY bookings.id DESC
    """).fetchall()


    # =====================================================
    # TECHNICIANS
    # =====================================================

    technicians = conn.execute("""
        SELECT *
        FROM technicians
        ORDER BY id DESC
    """).fetchall()


    # =====================================================
    # CUSTOMERS
    # =====================================================

    customers = conn.execute("""
        SELECT *
        FROM customers
        ORDER BY id DESC
    """).fetchall()


    # =====================================================
    # CONTACT MESSAGES
    # =====================================================

    contact_messages = conn.execute("""
        SELECT *
        FROM contact_messages
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "dashboard.html",

        name=session.get("name"),

        role=session.get("role"),

        bookings=bookings,

        technicians=technicians,

        customers=customers,

        contact_messages=contact_messages
    )


# =========================================================
# CUSTOMER MANAGEMENT
# =========================================================
# This route fixes:
# BuildError: Could not build url for endpoint 'customers'
# =========================================================

@app.route("/customers")
def customers():

    if session.get("role") != "Admin":

        return redirect(
            url_for("admin_login")
        )


    conn = get_db_connection()


    customer_list = conn.execute("""
        SELECT *
        FROM customers
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "customers.html",
        customers=customer_list
    )


# =========================================================
# DELETE CUSTOMER
# =========================================================

@app.route(
    "/delete-customer/<int:customer_id>",
    methods=["POST"]
)
def delete_customer(customer_id):

    if session.get("role") != "Admin":

        return "Access Denied", 403


    conn = get_db_connection()


    customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE id = ?
    """, (
        customer_id,
    )).fetchone()


    if customer is None:

        conn.close()

        return "Customer not found", 404


    conn.execute("""
        DELETE FROM customers
        WHERE id = ?
    """, (
        customer_id,
    ))


    conn.commit()

    conn.close()


    return redirect(
        url_for("dashboard")
    )


# =========================================================
# TECHNICIANS
# =========================================================

@app.route("/technicians")
def technicians():

    if session.get("role") != "Admin":

        return redirect(
            url_for("admin_login")
        )


    conn = get_db_connection()


    technician_list = conn.execute("""
        SELECT *
        FROM technicians
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "technicians.html",
        technicians=technician_list
    )


# =========================================================
# ADD TECHNICIAN
# =========================================================

@app.route(
    "/add-technician",
    methods=["GET", "POST"]
)
def add_technician():

    if session.get("role") != "Admin":

        return redirect(
            url_for("admin_login")
        )


    error = None


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        specialization = request.form.get(
            "specialization",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if (
            not name
            or not mobile
            or not username
            or not password
        ):

            error = (
                "Please fill all required fields."
            )


        else:

            conn = get_db_connection()


            try:

                conn.execute("""
                    INSERT INTO technicians
                    (
                        name,
                        mobile,
                        specialization,
                        username,
                        password,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    mobile,
                    specialization,
                    username,
                    password,
                    "Active",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ))


                conn.commit()

                conn.close()


                return redirect(
                    url_for("technicians")
                )


            except sqlite3.IntegrityError:

                conn.close()

                error = (
                    "Username already exists."
                )


    return render_template(
        "add_technician.html",
        error=error
    )


# =========================================================
# BOOK SERVICE
# =========================================================

@app.route(
    "/book-service",
    methods=["GET", "POST"]
)
def book_service():

    if request.method == "POST":

        customer_name = request.form.get(
            "customer_name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        ac_brand = request.form.get(
            "ac_brand",
            ""
        ).strip()

        ac_type = request.form.get(
            "ac_type",
            ""
        ).strip()

        service_type = request.form.get(
            "service_type",
            ""
        ).strip()

        preferred_date = request.form.get(
            "preferred_date",
            ""
        ).strip()

        preferred_time = request.form.get(
            "preferred_time",
            ""
        ).strip()

        problem = request.form.get(
            "problem",
            ""
        ).strip()


        date_part = datetime.now().strftime(
            "%Y%m%d"
        )


        conn = get_db_connection()


        cursor = conn.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE booking_id LIKE ?
        """, (
            f"OE-{date_part}-%",
        ))


        count = cursor.fetchone()[0] + 1


        booking_id = (
            f"OE-{date_part}-{count:04d}"
        )


        conn.execute("""
            INSERT INTO bookings
            (
                booking_id,
                customer_name,
                mobile,
                address,
                ac_brand,
                ac_type,
                service_type,
                preferred_date,
                preferred_time,
                problem,
                status,
                technician_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            booking_id,
            customer_name,
            mobile,
            address,
            ac_brand,
            ac_type,
            service_type,
            preferred_date,
            preferred_time,
            problem,
            "New",
            None,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))


        conn.commit()

        conn.close()


        return render_template(
            "booking_success.html",

            customer_name=customer_name,

            service_type=service_type,

            preferred_date=preferred_date,

            booking_id=booking_id
        )


    return render_template(
        "book_service.html"
    )


# =========================================================
# ASSIGN TECHNICIAN
# =========================================================

@app.route(
    "/assign-technician/<int:booking_id>",
    methods=["POST"]
)
def assign_technician(booking_id):

    if session.get("role") != "Admin":

        return redirect(
            url_for("admin_login")
        )


    technician_id = request.form.get(
        "technician_id"
    )


    if not technician_id:

        return redirect(
            url_for("dashboard")
        )


    conn = get_db_connection()


    technician = conn.execute("""
        SELECT id
        FROM technicians
        WHERE id = ?
        AND status = 'Active'
    """, (
        technician_id,
    )).fetchone()


    if technician is None:

        conn.close()

        return "Invalid Technician", 400


    conn.execute("""
        UPDATE bookings

        SET
            technician_id = ?,
            status = 'Assigned'

        WHERE id = ?
    """, (
        technician_id,
        booking_id
    ))


    conn.commit()

    conn.close()


    return redirect(
        url_for("dashboard")
    )


# =========================================================
# UPDATE BOOKING STATUS
# =========================================================

@app.route(
    "/update-status/<int:booking_id>",
    methods=["POST"]
)
def update_status(booking_id):

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    role = session.get("role")


    new_status = request.form.get(
        "status",
        ""
    )


    allowed_statuses = [

        "New",

        "Assigned",

        "Accepted",

        "On the Way",

        "Service Started",

        "Completed",

        "Cancelled"
    ]


    if new_status not in allowed_statuses:

        return "Invalid Status", 400


    conn = get_db_connection()


    # =====================================================
    # ADMIN
    # =====================================================

    if role == "Admin":

        conn.execute("""
            UPDATE bookings

            SET status = ?

            WHERE id = ?
        """, (
            new_status,
            booking_id
        ))


    # =====================================================
    # TECHNICIAN
    # =====================================================

    elif role == "Technician":

        technician_id = session.get(
            "technician_id"
        )


        technician_allowed = [

            "Accepted",

            "On the Way",

            "Service Started",

            "Completed"
        ]


        if new_status not in technician_allowed:

            conn.close()

            return (
                "Invalid Technician Status",
                400
            )


        booking = conn.execute("""
            SELECT id
            FROM bookings
            WHERE id = ?
            AND technician_id = ?
        """, (
            booking_id,
            technician_id
        )).fetchone()


        if booking is None:

            conn.close()

            return "Access Denied", 403


        conn.execute("""
            UPDATE bookings

            SET status = ?

            WHERE id = ?

            AND technician_id = ?
        """, (
            new_status,
            booking_id,
            technician_id
        ))


    else:

        conn.close()

        return "Access Denied", 403


    conn.commit()

    conn.close()


    if role == "Technician":

        return redirect(
            url_for("technician_jobs")
        )


    return redirect(
        url_for("dashboard")
    )


# =========================================================
# CONTACT
# =========================================================

@app.route(
    "/contact",
    methods=["GET", "POST"]
)
def contact():

    success = None

    error = None


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()


        if not name or not message:

            error = (
                "Name and message are required."
            )


        else:

            conn = get_db_connection()


            conn.execute("""
                INSERT INTO contact_messages
                (
                    name,
                    mobile,
                    email,
                    subject,
                    message,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                mobile,
                email,
                subject,
                message,
                "New",
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))


            conn.commit()

            conn.close()


            success = (
                "Thank you! Your message has been sent successfully."
            )


    return render_template(
        "contact.html",

        success=success,

        error=error
    )


# =========================================================
# TRACK BOOKING
# =========================================================

@app.route(
    "/track-booking",
    methods=["GET", "POST"]
)
def track_booking():

    booking = None

    error = None


    if request.method == "POST":

        booking_id = request.form.get(
            "booking_id",
            ""
        ).strip()


        if not booking_id:

            error = (
                "Please enter your Booking ID."
            )


        else:

            conn = get_db_connection()


            booking = conn.execute("""
                SELECT

                    bookings.*,

                    technicians.name
                        AS technician_name,

                    technicians.mobile
                        AS technician_mobile,

                    technicians.specialization
                        AS technician_specialization

                FROM bookings

                LEFT JOIN technicians

                ON bookings.technician_id =
                   technicians.id

                WHERE bookings.booking_id = ?

            """, (
                booking_id,
            )).fetchone()


            conn.close()


            if booking is None:

                error = (
                    "Booking ID not found. "
                    "Please check your Booking ID and try again."
                )


    return render_template(
        "track_booking.html",

        booking=booking,

        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()


    return redirect(
        url_for("login")
    )


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>

    <p>OSCAR ENGINEERS</p>

    <a href="/">Go Home</a>
    """, 404


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    return """
    <h1>500 - Internal Server Error</h1>

    <p>Please check the Flask terminal for the error.</p>

    <a href="/">Go Home</a>
    """, 500


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

# Initialize database when Flask starts.
# This works both locally and on Render/Gunicorn.
init_database()


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    print("")
    print("========================================")
    print("          OSCAR ENGINEERS")
    print("          Flask Server Started")
    print("========================================")
    print("")

    print("Home:")
    print("http://127.0.0.1:5000/")
    print("")

    print("Login Portal:")
    print("http://127.0.0.1:5000/login")
    print("")

    print("Hidden Admin Login:")
    print("http://127.0.0.1:5000/oscar-control-2026")
    print("")

    print("Customer Login:")
    print("http://127.0.0.1:5000/customer-login")
    print("")

    print("Customer Signup:")
    print("http://127.0.0.1:5000/customer-signup")
    print("")

    print("Technician Login:")
    print("http://127.0.0.1:5000/technician-login")
    print("")

    print("Track Booking:")
    print("http://127.0.0.1:5000/track-booking")
    print("")

    print("Admin Dashboard:")
    print("http://127.0.0.1:5000/dashboard")
    print("")

    print("========================================")


    app.run(
        debug=True
    )