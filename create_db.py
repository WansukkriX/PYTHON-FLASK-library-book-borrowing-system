import sqlite3

# สร้างฐานข้อมูลและตาราง
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

print("Database created and sample data inserted!")
