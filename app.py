from flask import Flask, render_template, request, redirect, session
from database import get_db_connection
from flask import jsonify
import razorpay
from qr_generator import generate_qr
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "canteen_secret_key_2026"

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET
    )
)


@app.route('/')
def home():

    if 'role' not in session:
        return render_template("login.html")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- STUDENT ----------------

    if session['role'] == "student":

        cursor.execute(
            "SELECT * FROM students WHERE id=%s",
            (session['user_id'],)
        )

        student = cursor.fetchone()

        if student:
            cursor.close()
            conn.close()
            return redirect('/student')

        session.clear()

    # ---------------- OWNER ----------------

    elif session['role'] == "owner":

        cursor.execute(
            "SELECT * FROM owners WHERE id=%s",
            (session['user_id'],)
        )

        owner = cursor.fetchone()

        if owner:
            cursor.close()
            conn.close()
            return redirect('/owner')

        session.clear()

    # ---------------- ADMIN ----------------

    elif session['role'] == "admin":

        cursor.execute(
            "SELECT * FROM admins WHERE id=%s",
            (session['user_id'],)
        )

        admin = cursor.fetchone()

        if admin:
            cursor.close()
            conn.close()
            return redirect('/admin')

        session.clear()

    cursor.close()
    conn.close()

    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login():

    role = request.form['role']
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if role == "student":

        cursor.execute(
            "SELECT * FROM students WHERE reg_no=%s AND dob=%s",
            (username, password)
        )

        student = cursor.fetchone()

        if student:

            session['role'] = 'student'
            session['user_id'] = student['id']
            session['name'] = student['student_name']
            session['reg_no'] = student['reg_no']

            return redirect('/student')

        return "Invalid Register Number or DOB"

    elif role == "owner":

        cursor.execute(
            "SELECT * FROM owners WHERE username=%s AND password=%s",
            (username, password)
        )

        owner = cursor.fetchone()

        if owner:

            session['role'] = 'owner'
            session['user_id'] = owner['id']

            return redirect('/owner')

        return "Invalid Owner Credentials"

    elif role == "admin":

        cursor.execute(
            "SELECT * FROM admins WHERE username=%s AND password=%s",
            (username, password)
        )

        admin = cursor.fetchone()

        if admin:

            session['role'] = 'admin'
            session['user_id'] = admin['id']

            return redirect('/admin')

        return "Invalid Admin Credentials"

    return redirect('/')


@app.route('/student')
def student():

    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (session['user_id'],)
    )

    student = cursor.fetchone()

    if not student:
        session.clear()
        cursor.close()
        conn.close()
        return redirect('/')

    cursor.execute("SELECT * FROM food_items")
    foods = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "student_dashboard.html",
        foods=foods
    )

@app.route('/owner')
def owner():

    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check owner still exists
    cursor.execute(
        "SELECT * FROM owners WHERE id=%s",
        (session['user_id'],)
    )

    owner = cursor.fetchone()

    if not owner:
        session.clear()
        cursor.close()
        conn.close()
        return redirect('/')

    # Load food items
    cursor.execute("SELECT * FROM food_items")
    foods = cursor.fetchall()

    # Load orders
    cursor.execute(
        "SELECT * FROM orders ORDER BY order_date DESC"
    )
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "owner_dashboard.html",
        foods=foods,
        orders=orders
    )
@app.route('/admin')
def admin():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total Students
    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()['total_students']

    # Total Owners
    cursor.execute("SELECT COUNT(*) AS total_owners FROM owners")
    total_owners = cursor.fetchone()['total_owners']

    # Total Orders
    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cursor.fetchone()['total_orders']

    # Total Paid Amount
    cursor.execute("""
        SELECT IFNULL(SUM(total_price),0) AS total_amount
        FROM orders
        WHERE payment_status='PAID'
    """)
    total_amount = cursor.fetchone()['total_amount']

    cursor.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_owners=total_owners,
        total_orders=total_orders,
        total_amount=total_amount
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

@app.route('/add_food', methods=['POST'])
def add_food():

    food_name = request.form['food_name']
    category = request.form['category']
    price = request.form['price']

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO food_items
    (food_name, category, price)
    VALUES (%s,%s,%s)
    """

    cursor.execute(sql,(food_name,category,price))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/owner')

@app.route('/menu')
def menu():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM food_items")

    foods = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'menu.html',
        foods=foods
    )

@app.route('/delete_food/<int:id>', methods=['POST'])
def delete_food(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM food_items WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/owner')

@app.route('/place_order/<int:food_id>', methods=['POST'])
def place_order(food_id):

    if session.get('role') != 'student':
        return redirect('/')

    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM food_items WHERE id=%s",
        (food_id,)
    )

    food = cursor.fetchone()

    if not food:
        return "Food item not found"

    total = float(food['price']) * quantity

    cursor.execute(
        """
        INSERT INTO orders
        (student_reg_no, food_id, food_name, price,
         quantity, total_price)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            session['reg_no'],      # Student ID from session
            food['id'],              # Food ID
            food['food_name'],       # Food Name
            food['price'],           # Price
            quantity,                # Quantity
            total                    # Total Price
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/menu')

@app.route('/accept_order/<int:order_id>')
def accept_order(order_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE orders SET status='Accepted' WHERE id=%s",
        (order_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/owner')


@app.route('/reject_order/<int:order_id>')
def reject_order(order_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE orders SET status='Rejected' WHERE id=%s",
        (order_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/owner')

@app.route('/my_orders')
def my_orders():

    if session.get('role') != 'student':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE student_reg_no = %s
        ORDER BY id DESC
        """,
        (session['reg_no'],)
    )

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'my_orders.html',
        orders=orders
    )

@app.route('/statistics')
def statistics():

    if session.get('role') != 'owner':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cursor.fetchone()['total_orders']

    cursor.execute(
        "SELECT COUNT(*) AS pending_orders FROM orders WHERE status='Pending'"
    )
    pending_orders = cursor.fetchone()['pending_orders']

    cursor.execute(
        "SELECT COUNT(*) AS accepted_orders FROM orders WHERE status='Accepted'"
    )
    accepted_orders = cursor.fetchone()['accepted_orders']

    cursor.execute(
        """
        SELECT IFNULL(SUM(total_price),0) AS revenue
        FROM orders
        WHERE status='Accepted'
        """
    )
    revenue = cursor.fetchone()['revenue']

    cursor.close()
    conn.close()

    return render_template(
        'statistics.html',
        total_orders=total_orders,
        pending_orders=pending_orders,
        accepted_orders=accepted_orders,
        revenue=revenue
    )

@app.route('/create_payment/<int:order_id>')
def create_payment(order_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT total_price FROM orders WHERE id=%s",
        (order_id,)
    )

    order = cursor.fetchone()

    amount = int(float(order['total_price']) * 100)

    razorpay_order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    cursor.execute("""
        UPDATE orders
        SET razorpay_order_id=%s
        WHERE id=%s
    """, (
        razorpay_order['id'],
        order_id
    ))

    conn.commit()

    return jsonify({
        "order_id": razorpay_order['id'],
        "amount": amount,
        "key": RAZORPAY_KEY_ID
    })

@app.route('/verify_payment', methods=['POST'])
def verify_payment():

    data = request.get_json()

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE orders
            SET payment_status='PAID',
                razorpay_payment_id=%s,
                razorpay_order_id=%s
            WHERE id=%s
        """, (
            data['razorpay_payment_id'],
            data['razorpay_order_id'],
            data['canteen_order_id']
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success"
        })

    except Exception as e:

        print("verification error:",e)

        return jsonify({
            "status": "failed",
            "message": str(e)
        })
@app.route('/deliver_order/<int:order_id>')
def deliver_order(order_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE orders SET status='Delivered' WHERE id=%s",
        (order_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/owner')

@app.route("/ticket/<int:order_id>")
def ticket(order_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE id=%s
    """,(order_id,))

    order = cursor.fetchone()

    cursor.close()
    conn.close()

    if order is None:
        return "Order Not Found"

    if order["payment_status"] != "PAID":
        return "Payment Pending"

    if order["status"] != "Accepted":
        return "Order Not Accepted"

    image = generate_qr(order_id)

    return render_template(
        "qr_ticket.html",
        order=order,
        image=image
    )

@app.route("/verify_ticket/<int:order_id>")
def verify_ticket(order_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE id=%s
    """,(order_id,))

    order = cursor.fetchone()

    cursor.close()
    conn.close()

    if order is None:
        return "<h1>❌ Invalid Ticket</h1>"

    if order["payment_status"] != "PAID":
        return "<h1>❌ Payment Pending</h1>"

    if order["status"] == "Delivered":
        return "<h1>❌ Ticket Already Used</h1>"

    if order["status"] != "Accepted":
        return "<h1>❌ Order Not Accepted</h1>"

    return render_template(
        "ticket_verified.html",
        order=order
    )

@app.route('/students')
def students():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY reg_no")
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'students.html',
        students=students
    )

@app.route('/add_student', methods=['POST'])
def add_student():

    reg_no = request.form['reg_no']
    student_name = request.form['student_name']
    dob = request.form['dob']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO students
        (reg_no,student_name,dob)
        VALUES(%s,%s,%s)
    """,(reg_no,student_name,dob))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/students')

@app.route('/delete_student/<int:id>')
def delete_student(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/students')

@app.route('/edit_student/<int:id>', methods=['GET','POST'])
def edit_student(id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':

        reg_no = request.form['reg_no']
        student_name = request.form['student_name']
        dob = request.form['dob']

        cursor.execute("""
            UPDATE students
            SET reg_no=%s,
                name=%s,
                dob=%s
            WHERE id=%s
        """,(reg_no,student_name,dob,id))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect('/students')

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'edit_student.html',
        student=student
    )

@app.route('/update_student/<int:id>', methods=['POST'])
def update_student(id):

    reg_no = request.form['reg_no']
    student_name = request.form['student_name']
    dob = request.form['dob']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET reg_no=%s,
        student_name=%s,
        dob=%s
    WHERE id=%s
    """,(reg_no, student_name, dob, id))

    conn.commit()
    conn.close()

    return redirect('/students')

@app.route('/owners')
def owners():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM owners")
    owners = cursor.fetchall()

    conn.close()

    return render_template(
        "owners.html",
        owners=owners
    )

@app.route('/add_owner', methods=['POST'])
def add_owner():

    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO owners(username,password)
    VALUES(%s,%s)
    """,(username,password))

    conn.commit()
    conn.close()

    return redirect('/owners')

@app.route('/delete_owner/<int:id>')
def delete_owner(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM owners WHERE id=%s",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/owners')

@app.route('/edit_owner/<int:id>')
def edit_owner(id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM owners WHERE id=%s",
        (id,)
    )

    owner = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_owner.html",
        owner=owner
    )

@app.route('/update_owner/<int:id>', methods=['POST'])
def update_owner(id):

    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE owners
    SET username=%s,
        password=%s
    WHERE id=%s
    """,(username,password,id))

    conn.commit()
    conn.close()

    return redirect('/owners')
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
