from flask import Flask, render_template, request,redirect ,jsonify
import sqlite3

app = Flask(__name__)

# ฟังก์ชันสำหรับเชื่อมต่อกับฐานข้อมูล SQLite
def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row  # เพื่อให้สามารถใช้ชื่อคอลัมน์ได้ในผลลัพธ์
    return conn

# ฟังก์ชันสร้างฐานข้อมูล (ถ้าไม่พบ)
def create_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    # สร้างตารางสมาชิก
    c.execute('''
    CREATE TABLE IF NOT EXISTS tb_member (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        m_user TEXT,
        m_pass TEXT,
        m_name TEXT,
        m_phone TEXT
    )
    ''')

    # สร้างตารางหนังสือ
    c.execute('''
    CREATE TABLE IF NOT EXISTS tb_book (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        b_id TEXT,
        b_name TEXT,
        b_writer TEXT,
        b_category TEXT,
        b_price REAL
    )
    ''')

    # สร้างตารางการยืม-คืนหนังสือ
    c.execute('''
    CREATE TABLE IF NOT EXISTS tb_borrow_book (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        b_date_br TEXT,
        b_date_rt TEXT,
        b_id TEXT,
        m_user TEXT,
        br_fine REAL,
        FOREIGN KEY (b_id) REFERENCES tb_book(b_id),
        FOREIGN KEY (m_user) REFERENCES tb_member(m_user)
    )
    ''')

    conn.commit()
    conn.close()

# เรียกใช้ฟังก์ชันสร้างฐานข้อมูลก่อนเริ่มทำงาน
create_db()

# หน้าแรกที่จะแสดงสมาชิกและหนังสือ
@app.route('/')
def index():
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM tb_member').fetchall()
    books = conn.execute('SELECT * FROM tb_book').fetchall()
    
    # ดึงข้อมูลการยืม-คืนหนังสือ
    borrows = conn.execute('''
        SELECT bb.*, b.b_name, m.m_name 
        FROM tb_borrow_book bb
        JOIN tb_book b ON bb.b_id = b.b_id
        JOIN tb_member m ON bb.m_user = m.m_user
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', members=members, books=books, borrows=borrows)

# ฟังก์ชันสำหรับการยืมหนังสือ
@app.route('/borrow_book', methods=['GET', 'POST'])
def borrow_book():
    if request.method == 'POST':
        b_id = request.form['b_id']
        m_user = request.form['m_user']
        b_date_br = request.form['b_date_br']
        
        conn = get_db_connection()
        try:
            # ตรวจสอบว่าหนังสือมีอยู่ในระบบหรือไม่
            book = conn.execute('SELECT * FROM tb_book WHERE b_id = ?', (b_id,)).fetchone()
            if not book:
                return jsonify('Error: Book not found!'), 404

            # ตรวจสอบว่าสมาชิกมีอยู่ในระบบหรือไม่
            member = conn.execute('SELECT * FROM tb_member WHERE m_user = ?', (m_user,)).fetchone()
            if not member:
                return jsonify('Error: Member not found!'), 404

            # ตรวจสอบว่าหนังสือถูกยืมไปแล้วหรือไม่
            borrowed = conn.execute('''
                SELECT * FROM tb_borrow_book 
                WHERE b_id = ? AND b_date_rt IS NULL
            ''', (b_id,)).fetchone()
            if borrowed:
                return jsonify('Error: Book is already borrowed!'), 400

            # ตรวจสอบจำนวนหนังสือที่สมาชิกยืมอยู่
            current_borrows = conn.execute('''
                SELECT COUNT(*) as count FROM tb_borrow_book 
                WHERE m_user = ? AND b_date_rt IS NULL
            ''', (m_user,)).fetchone()
            
            if current_borrows['count'] >= 3:  # สมมติว่ายืมได้สูงสุด 3 เล่ม
                return jsonify('Error: Member has reached maximum borrow limit!'), 400

            # เพิ่มข้อมูลการยืม
            conn.execute('''
                INSERT INTO tb_borrow_book 
                (b_id, m_user, b_date_br, b_date_rt, br_fine) 
                VALUES (?, ?, ?, NULL, 0)
            ''', (b_id, m_user, b_date_br))
            
            conn.commit()
            return jsonify('Book borrowed successfully!'), 200

        except Exception as e:
            conn.rollback()
            return jsonify(f'Error: {str(e)}'), 500
        finally:
            conn.close()

    # GET request - แสดงข้อมูลสำหรับ dropdowns
    conn = get_db_connection()
    books = conn.execute('''
        SELECT b.* FROM tb_book b
        LEFT JOIN tb_borrow_book bb ON b.b_id = bb.b_id AND bb.b_date_rt IS NULL
        WHERE bb.b_id IS NULL
    ''').fetchall()
    
    members = conn.execute('SELECT * FROM tb_member').fetchall()
    conn.close()
    
    return render_template('borrow_book.html', books=books, members=members)


# add book
# เพิ่มหนังสือ
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        b_id = request.form['b_id']
        b_name = request.form['b_name']
        b_writer = request.form['b_writer']
        b_category = request.form['b_category']
        b_price = float(request.form['b_price'])  # แปลงเป็น float

        conn = get_db_connection()
        
        try:
            # Check if book ID already exists
            existing_book = conn.execute('SELECT * FROM tb_book WHERE b_id = ?', (b_id,)).fetchone()
            if existing_book:
                conn.close()
                return 'Error: Book ID already exists!'
            
            # Add new book
            conn.execute('''INSERT INTO tb_book (b_id, b_name, b_writer, b_category, b_price) 
                            VALUES (?, ?, ?, ?, ?)''', 
                         (b_id, b_name, b_writer, b_category, b_price))
            conn.commit()
            return redirect('/')  # ไปยังหน้าแรกหลังจากเพิ่มหนังสือ
            
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return f'Error: {str(e)}'

        finally:
            conn.close()

    return render_template('add_book.html')


# dashbord
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()

    # ดึงข้อมูลสมาชิกทั้งหมด
    members = conn.execute('SELECT * FROM tb_member').fetchall()

    # ดึงข้อมูลหนังสือทั้งหมด
    books = conn.execute('SELECT * FROM tb_book').fetchall()

    # ดึงข้อมูลการยืม-คืนหนังสือทั้งหมด
    borrows = conn.execute('SELECT * FROM tb_borrow_book').fetchall()

    # นับจำนวนครั้งที่ยืม-คืน
    borrow_count = len(borrows)

    # หาหนังสือที่ค้างส่ง (ยังไม่คืน)
    overdue_books = conn.execute('SELECT * FROM tb_borrow_book WHERE b_date_rt IS NULL').fetchall()

    conn.close()
    return render_template('dashboard.html', members=members, books=books, borrow_count=borrow_count, overdue_books=overdue_books)


# เพิ่มสมาชิก
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        m_user = request.form['m_user']
        m_pass = request.form['m_pass']
        m_name = request.form['m_name']
        m_phone = request.form['m_phone']

        conn = get_db_connection()
        
        try:
            # ตรวจสอบชื่อผู้ใช้ซ้ำ
            existing_user = conn.execute('SELECT * FROM tb_member WHERE m_user = ?', (m_user,)).fetchone()
            if existing_user:
                conn.close()
                return 'Error: Username already exists!'

            # เพิ่มข้อมูลสมาชิกใหม่
            conn.execute('INSERT INTO tb_member (m_user, m_pass, m_name, m_phone) VALUES (?, ?, ?, ?)',
                         (m_user, m_pass, m_name, m_phone))
            conn.commit()
            return redirect('/')  # ไปยังหน้าแรกหลังจากเพิ่มสมาชิก
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
            return f'Error: {str(e)}'

        finally:
            conn.close()

    return render_template('add_member.html')


# ฟังก์ชันสำหรับการคืนหนังสือ
@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        b_id = request.form['b_id']
        m_user = request.form['m_user']
        b_date_rt = request.form['b_date_rt']
        br_fine = float(request.form['br_fine'])  # แปลงเป็น float

        conn = get_db_connection()

        try:
            # ตรวจสอบว่าหนังสือถูกยืมไปแล้วหรือไม่
            borrowed = conn.execute('''
                SELECT * FROM tb_borrow_book 
                WHERE b_id = ? AND m_user = ? AND b_date_rt IS NULL
            ''', (b_id, m_user)).fetchone()

            if not borrowed:
                return render_template('return_book.html', message='Error: This book was not borrowed or already returned.')

            # อัพเดตสถานะการคืนหนังสือ
            conn.execute('''
                UPDATE tb_borrow_book 
                SET b_date_rt = ?, br_fine = ? 
                WHERE b_id = ? AND m_user = ? AND b_date_rt IS NULL
            ''', (b_date_rt, br_fine, b_id, m_user))

            conn.commit()

            return render_template('return_book.html', message='Book returned successfully!')

        except Exception as e:
            conn.rollback()
            return render_template('return_book.html', message=f'Error: {str(e)}')

        finally:
            conn.close()

    return render_template('return_book.html')

if __name__ == "__main__":
    app.run(debug=True)
