from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import MySQLdb.cursors
           
app = Flask(__name__)
app.secret_key = 'secretkey123'

#dekorator admin
def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'role' not in session or session['role'] != "admin":
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

#dekorator user
def role_required(role):
    def wrapper(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'role' not in session:
                return redirect(url_for('login'))
            if session['role'] != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrap
    return wrapper

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if 'role' not in session:
                return redirect('/login')
            if session['role'] != role:
                return redirect('/login')
            return f(*args, **kwargs)
        return wrap
    return decorator

@app.route('/')
def home():
    return redirect('/login')

# Database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_tiket_bioskop_yoga'

mysql = MySQL(app)

#REGIS
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user_yoga(nama,email,password,role) VALUES(%s,%s,%s,%s)",
                    (nama,email,password,role))
        mysql.connection.commit()
        cur.close()

        return redirect('/login')

    return render_template('register.html')


#LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Semua field harus diisi!")
            return render_template('login.html')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM user_yoga WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user is None:
            flash("Email tidak ditemukan!")
            return render_template('login.html')

        if not check_password_hash(user['password'], password):
            flash("Password salah!")
            return render_template('login.html')

        # Login berhasil
        session['user_id'] = user['user_id']
        session['nama'] = user['nama']
        session['role'] = user['role']

        if user['role'] == 'admin':
            return redirect('/admin')
        else:
            return redirect('/user')

    return render_template('login.html')


#ADMIN
@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM film_oga")
    data = cur.fetchall()
    cur.close()

    return render_template(
        'admin_dashboard.html',
        nama=session['nama'],
        films=data
    )

#HALAMAN USER
@app.route('/user')
@role_required('user')
def user():

    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # Ambil semua film
    cur.execute("SELECT * FROM film_oga")
    films = cur.fetchall()

    # Ambil riwayat pemesanan (JOIN 2 tabel)
    cur.execute("""
        SELECT p.*, f.judul_film
        FROM pemesanan_yoga p
        JOIN jadwal_tayang_yoga j ON p.jadwal_id = j.jadwal_id
        JOIN film_oga f ON j.film_id = f.film_id
        WHERE p.user_id = %s
        ORDER BY p.pemesanan_id DESC
    """, (user_id,))

    transaksi = cur.fetchall()
    cur.close()

    return render_template(
        'user_dashboard.html',
        nama=session.get('nama'),
        films=films,
        transaksi=transaksi
    )

@app.route('/admin/film')
@role_required('admin')
def film():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM film_oga")
    data = cur.fetchall()
    cur.close()
    return render_template('film_admin.html', film=data)

#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)