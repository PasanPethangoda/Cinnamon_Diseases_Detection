import os
import json
import numpy as np
from keras.models import load_model
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from tensorflow.keras.preprocessing.image import load_img, img_to_array # type: ignore
import mysql.connector # type: ignore
from mysql.connector import Error # type: ignore
from flask_mail import Mail, Message # type: ignore

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = 'image'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size is 16MB
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234'


# -----------Flask-Mail configuration-------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pasanpethangoda@gmail.com'
app.config['MAIL_PASSWORD'] = 'emkg nzbo gbrv clay'
app.config['MAIL_DEFAULT_SENDER'] = ('Dr.CINNAMON', 'pasanpethangoda@gmail.com')

mail = Mail(app)

# -----------Flask-Mail configuration-------------------



#--------------Load the model-----------------------
model = load_model('model_2.h5')
with open('treatments.json') as f:
    treatments = json.load(f)  # Load the JSON file

with open('briefs.json') as f:
    briefs = json.load(f)  # Load the JSON file

#---------------- Define class labels----------------
labels = {0: 'Healthy Cinnamon', 1: 'Not Related', 2: 'RoughBark Disease', 3: 'StripeCanker Disease'}

#--------Get the Prediction -----------
def getResult(image_path):
    img = load_img(image_path, target_size=(225, 225))
    x = img_to_array(img)
    x = x.astype('float32') / 255.
    x = np.expand_dims(x, axis=0)
    predictions = model.predict(x)[0]
    return predictions
#--------Get the Prediction -----------


#--------Database Connection - Start--------
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='cinnamon',
            user='root',
            password=''
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    return None
#--------Database Connection - End--------


#------------Feedback GET method in Index page---------
@app.route('/', methods=['GET'])
def index():

    connection = get_db_connection()
    feedback_list = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, message FROM feedback")
        feedback_list = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('index.html', feedback_list=feedback_list)
#------------Feedback GET method in Index Page---------


@app.route('/detect', methods=['GET'])
def detect():
    return render_template('detect.html')


#-------Prediction Section - Start---------------
@app.route('/predict', methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
        f.save(file_path)
        predictions = getResult(file_path)
        predicted_label = labels[np.argmax(predictions)]
        treatment = treatments[predicted_label]['treatment']
        brief = briefs[predicted_label]['brief']
        return render_template('result.html', label=predicted_label, treatment=treatment, brief=brief, filepath=f.filename)
    return None
#-------Prediction Section - End---------------



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/image/<filename>')
def image_file(filename):
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)


#-------------Feedback Section - Start -----------------------
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    feedback_message = None
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message']
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO feedback (name, message) VALUES (%s, %s)", (name, message))
            connection.commit()
            cursor.close()
            connection.close()
            feedback_message = "Feedback submitted successfully!"
        else:
            feedback_message = "Failed to submit feedback. Please try again later."

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, message FROM feedback")
        feedback_list = cursor.fetchall()
        cursor.close()
        connection.close()

    return render_template('feedback.html', feedback_message=feedback_message, feedback_list=feedback_list)
#--------------Feedback Section - End -------------------------



#------Admin Login & Logout section-------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/admin/logout', methods=['GET'])
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))
#------Admin Login & Logout section-------


#--------Fertilizer (Product) View  by Client Side---------
@app.route('/products', methods=['GET'])
def products():
    connection = get_db_connection()
    products_list = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, description, price, image FROM products")
        products_list = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('products.html', products_list=products_list)
#--------Fertilizer (Product) View  by Client Side---------


#-----------View Fertilizer (Product) by Admin Side------------
@app.route('/admin', methods=['GET'])
def admin():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    products_list = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, description, price, image FROM products")
        products_list = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('admin.html', products_list=products_list)
#-----------View Fertilizer (Product) by Admin Side------------
   
#--------------Insert Fertilizer (Product) section - Start-----------------
@app.route('/insert_product', methods=['POST'])
def insert_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']

        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['IMAGE_FOLDER'], image_filename)
            image.save(image_path)

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO products (name, description, price, image) VALUES (%s, %s, %s, %s)",
                               (name, description, price, image_filename))
                connection.commit()
                cursor.close()
                connection.close()
                flash('Product Added Successfully!', 'success')
            except Error as e:
                flash(f'Failed to insert product: {e}', 'error')
        else:
            flash('Failed to connect to the database.', 'error')

        return redirect(url_for('admin'))
    return None
#-----------Insert Fertilizer (Product) section - End--------------




#------Update Fertilizer (Product) section - Start--------------
@app.route('/update_product/<int:id>', methods=['GET'])
def update_product(id):
    connection = get_db_connection()
    product = None
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, description, price, image FROM products WHERE id = %s", (id,))
        product = cursor.fetchone()
        cursor.close()
        connection.close()
    return render_template('admin.html', product=product)


@app.route('/update_product/<int:id>', methods=['POST'])
def update_product_post(id):
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    image = request.files['image']

    filename = None
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['IMAGE_FOLDER'], filename))

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        if filename:
            cursor.execute("""
                UPDATE products
                SET name = %s, description = %s, price = %s, image = %s
                WHERE id = %s
            """, (name, description, price, filename, id))
        else:
            cursor.execute("""
                UPDATE products
                SET name = %s, description = %s, price = %s
                WHERE id = %s
            """, (name, description, price, id))
        connection.commit()
        cursor.close()
        connection.close()
    flash('Product Updated Successfully!', 'success')
    return redirect(url_for('admin'))
#-----------------Update Fertilizer (Product) section - End-----------------



#-------------Delete Fertilizer (Product) section - Start---------------------
@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Check for related rows in the orders table
        cursor.execute("SELECT COUNT(*) FROM orders WHERE product_id = %s", (id,))
        order_count = cursor.fetchone()[0]
        
        if order_count > 0:
            cursor.close()
            connection.close()
            flash('Cannot delete this product. There are existing orders for this product.', 'danger')
            return redirect(url_for('admin'))
        
        # Delete the product
        cursor.execute("DELETE FROM products WHERE id = %s", (id,))
        connection.commit()
        cursor.close()
        connection.close()
        
    flash('Product Deleted Successfully!', 'success')
    return redirect(url_for('admin'))
#--------------Delete Fertilizer (Product) section - End-----------------------




#--------------Buy Fertilizer (Product) section - Start---------------
@app.route('/buy', methods=['POST'])
def buy():
    product_id = request.form['product_id']
    quantity = request.form['quantity']
    client_name = request.form['client_name']
    client_email = request.form['client_email']
    client_address = request.form['client_address']
    client_mobile = request.form['client_mobile']
    card_number = request.form['card_number']
    card_expiry = request.form['card_expiry']
    card_cvv = request.form['card_cvv']
    price = request.form['price']

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Fetch product name
        cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product_name = cursor.fetchone()[0]
        
        # Insert order into database
        cursor.execute("""
            INSERT INTO orders (product_id, quantity, client_name, client_email, client_address, client_mobile, card_number, card_expiry, card_cvv, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, 
        (product_id, quantity, client_name, client_email, client_address, client_mobile, card_number, card_expiry, card_cvv, price))
        connection.commit()
        cursor.close()
        connection.close()

        # Send confirmation email
        send_email(client_name, client_email, product_id, product_name, quantity, price)

    return redirect(url_for('products'))


def send_email(client_name, client_email, product_id, product_name, quantity, price):
    msg = Message("Order Confirmation",
                  recipients=[client_email])

    #Send email function
    msg.body = f"""
    Dear {client_name},

    Your Payment Has Been Successfully - Thank you !

    Order Details:
    - Product ID: {product_id}
    - Product Name: {product_name}
    - Quantity: {quantity}
    - Total Price: Rs {price}

    We appreciate your business and hope you enjoy your purchase !

    Best Regards,
    Dr. CINNAMON.......!
    """

    try:
        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

#-------------Buy Fertilizer (Product) section - End-----------------------------



#--------Order View by Admin - Start---------

@app.route('/orders', methods=['GET'])
def orders():
    connection = get_db_connection()
    orders_list = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT orders.id, products.name, orders.quantity, orders.client_name, orders.client_email,
                   orders.client_address, orders.client_mobile, orders.card_number, orders.card_expiry, orders.card_cvv, orders.price
            FROM orders
            JOIN products ON orders.product_id = products.id
        """)
        orders_list = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('orders.html', orders_list=orders_list)

#--------Order View by Admin - End---------


if __name__ == '__main__':
    app.run(debug=True)
