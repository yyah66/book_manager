from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation

import config

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.SECRET_KEY


def get_conn():
    """Create a psycopg connection with dict rows for template-friendly access."""
    return psycopg.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        row_factory=dict_row,
    )


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    sql = """
        SELECT b.book_id,
               b.title,
               a.name AS author,
               c.name AS category,
               b.isbn,
               b.stock
        FROM book b
        LEFT JOIN author a ON b.author_id = a.author_id
        LEFT JOIN category c ON b.category_id = c.category_id
    """
    params = []
    if q:
        sql += " WHERE (b.title ILIKE %s OR a.name ILIKE %s OR c.name ILIKE %s)"
        like = f"%{q}%"
        params = [like, like, like]
    sql += " ORDER BY b.book_id DESC"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return render_template("index.html", rows=rows, q=q)


@app.route("/book/<int:book_id>")
def book_detail(book_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT b.*,
                   a.name AS author_name,
                   c.name AS category_name
            FROM book b
            LEFT JOIN author a ON b.author_id = a.author_id
            LEFT JOIN category c ON b.category_id = c.category_id
            WHERE b.book_id = %s
            """,
            (book_id,),
        )
        book = cur.fetchone()
        if not book:
            flash("图书不存在")
            return redirect(url_for("index"))
        cur.execute(
            """
            SELECT r.review_id,
                   u.username,
                   r.rating,
                   r.content,
                   r.created_at
            FROM review r
            JOIN "user" u ON r.user_id = u.user_id
            WHERE r.book_id = %s
            ORDER BY r.created_at DESC
            """,
            (book_id,),
        )
        reviews = cur.fetchall()
    return render_template("book_detail.html", book=book, reviews=reviews)


@app.route("/book/new", methods=["GET", "POST"])
def new_book():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT author_id, name FROM author ORDER BY name")
        authors = cur.fetchall()
        cur.execute("SELECT category_id, name FROM category ORDER BY name")
        categories = cur.fetchall()
    if request.method == "POST":
        title = request.form["title"].strip()
        author_name = request.form.get("author_name", "").strip()
        category_id = request.form.get("category_id") or None
        isbn = request.form.get("isbn") or None
        stock = int(request.form.get("stock") or 0)
        with get_conn() as conn, conn.cursor() as cur:
            author_id = None
            if author_name:
                cur.execute("SELECT author_id FROM author WHERE name = %s", (author_name,))
                existing = cur.fetchone()
                if existing:
                    author_id = existing["author_id"]
                else:
                    cur.execute(
                        "INSERT INTO author (name) VALUES (%s) RETURNING author_id",
                        (author_name,),
                    )
                    author_id = cur.fetchone()["author_id"]
            cur.execute(
                """
                INSERT INTO book (title, author_id, category_id, isbn, stock)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (title, author_id, category_id, isbn, stock),
            )
            conn.commit()
        flash("新增图书成功")
        return redirect(url_for("index"))
    return render_template(
        "book_form.html",
        mode="new",
        authors=authors,
        categories=categories,
        book=None,
    )


@app.route("/book/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT b.*,
                   a.name AS author_name
            FROM book b
            LEFT JOIN author a ON b.author_id = a.author_id
            WHERE b.book_id = %s
            """,
            (book_id,),
        )
        book = cur.fetchone()
        if not book:
            flash("图书不存在")
            return redirect(url_for("index"))
        cur.execute("SELECT author_id, name FROM author ORDER BY name")
        authors = cur.fetchall()
        cur.execute("SELECT category_id, name FROM category ORDER BY name")
        categories = cur.fetchall()
    if request.method == "POST":
        title = request.form["title"].strip()
        author_name = request.form.get("author_name", "").strip()
        category_id = request.form.get("category_id") or None
        isbn = request.form.get("isbn") or None
        stock = int(request.form.get("stock") or 0)
        with get_conn() as conn, conn.cursor() as cur:
            author_id = None
            if author_name:
                cur.execute("SELECT author_id FROM author WHERE name = %s", (author_name,))
                existing = cur.fetchone()
                if existing:
                    author_id = existing["author_id"]
                else:
                    cur.execute(
                        "INSERT INTO author (name) VALUES (%s) RETURNING author_id",
                        (author_name,),
                    )
                    author_id = cur.fetchone()["author_id"]
            cur.execute(
                """
                UPDATE book
                SET title = %s,
                    author_id = %s,
                    category_id = %s,
                    isbn = %s,
                    stock = %s
                WHERE book_id = %s
                """,
                (title, author_id, category_id, isbn, stock, book_id),
            )
            conn.commit()
        flash("更新成功")
        return redirect(url_for("index"))
    return render_template(
        "book_form.html",
        mode="edit",
        authors=authors,
        categories=categories,
        book=book,
    )


@app.route("/book/<int:book_id>/delete")
def delete_book(book_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
        conn.commit()
    flash("已删除")
    return redirect(url_for("index"))


@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        role_id = request.form.get("role_id") or None
        with get_conn() as conn, conn.cursor() as cur:
            if not role_id:
                cur.execute("SELECT role_id FROM role WHERE name = %s", ("user",))
                role = cur.fetchone()
                role_id = role["role_id"] if role else None
            else:
                role_id = int(role_id)
            try:
                cur.execute(
                    'INSERT INTO "user" (username, email, role_id) VALUES (%s, %s, %s)',
                    (username, email, role_id),
                )
                conn.commit()
                flash("用户新增成功")
            except UniqueViolation:
                conn.rollback()
                flash("用户名或邮箱已存在")
        return redirect(url_for("users"))
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            '''
            SELECT u.user_id, u.username, u.email, r.name AS role_name
            FROM "user" u
            LEFT JOIN role r ON u.role_id = r.role_id
            ORDER BY u.user_id DESC
            '''
        )
        rows = cur.fetchall()
        cur.execute("SELECT role_id, name FROM role ORDER BY role_id")
        roles = cur.fetchall()
    return render_template("users.html", rows=rows, roles=roles)


@app.route("/authors", methods=["GET", "POST"])
def authors():
    if request.method == "POST":
        name = request.form["name"].strip()
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO author (name) VALUES (%s)", (name,))
            conn.commit()
        flash("作者新增成功")
        return redirect(url_for("authors"))
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM author ORDER BY author_id DESC")
        rows = cur.fetchall()
    return render_template("authors.html", rows=rows)


@app.route("/categories", methods=["GET", "POST"])
def categories():
    if request.method == "POST":
        name = request.form["name"].strip()
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO category (name) VALUES (%s)", (name,))
            conn.commit()
        flash("分类新增成功")
        return redirect(url_for("categories"))
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM category ORDER BY category_id DESC")
        rows = cur.fetchall()
    return render_template("categories.html", rows=rows)


@app.route("/borrows")
def borrows():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT bo.borrow_id,
                   u.username,
                   b.title,
                   bo.borrowed_at,
                   bo.due_at,
                   bo.returned_at
            FROM borrow bo
            JOIN "user" u ON bo.user_id = u.user_id
            JOIN book b ON bo.book_id = b.book_id
            ORDER BY bo.borrow_id DESC
            """
        )
        rows = cur.fetchall()
    return render_template("borrows.html", rows=rows)


@app.route("/book/<int:book_id>/borrow", methods=["POST"])
def borrow_book(book_id: int):
    raw_user = request.form.get("user_id", "").strip()
    if not raw_user:
        flash("请输入用户ID")
        return redirect(url_for("book_detail", book_id=book_id))
    try:
        user_id = int(raw_user)
    except ValueError:
        flash("用户ID应为数字")
        return redirect(url_for("book_detail", book_id=book_id))
    try:
        days = int(request.form.get("days", 14))
    except ValueError:
        days = 14
    if days <= 0:
        days = 14
    due_at = datetime.datetime.now() + datetime.timedelta(days=days)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute('SELECT user_id FROM "user" WHERE user_id = %s', (user_id,))
        if not cur.fetchone():
            flash("用户不存在，请先在“用户”页添加。")
            return redirect(url_for("book_detail", book_id=book_id))
        cur.execute("SELECT stock FROM book WHERE book_id = %s", (book_id,))
        row = cur.fetchone()
        if not row:
            flash("图书不存在")
            return redirect(url_for("index"))
        if row["stock"] <= 0:
            flash("库存不足")
            return redirect(url_for("book_detail", book_id=book_id))
        cur.execute("UPDATE book SET stock = stock - 1 WHERE book_id = %s", (book_id,))
        cur.execute(
            "INSERT INTO borrow (user_id, book_id, due_at) VALUES (%s, %s, %s)",
            (user_id, book_id, due_at),
        )
        conn.commit()
    flash("借阅成功")
    return redirect(url_for("book_detail", book_id=book_id))


@app.route("/borrow/<int:borrow_id>/return")
def return_book(borrow_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT book_id, returned_at FROM borrow WHERE borrow_id = %s",
            (borrow_id,),
        )
        row = cur.fetchone()
        if not row:
            flash("记录不存在")
            return redirect(url_for("borrows"))
        book_id = row["book_id"]
        returned_at = row["returned_at"]
        if returned_at:
            flash("已归还")
            return redirect(url_for("borrows"))
        cur.execute(
            "UPDATE borrow SET returned_at = CURRENT_TIMESTAMP WHERE borrow_id = %s",
            (borrow_id,),
        )
        cur.execute("UPDATE book SET stock = stock + 1 WHERE book_id = %s", (book_id,))
        conn.commit()
    flash("归还成功")
    return redirect(url_for("borrows"))


@app.route("/book/<int:book_id>/review", methods=["POST"])
def add_review(book_id: int):
    user_id = int(request.form["user_id"])
    rating = int(request.form["rating"])
    content = request.form.get("content", "").strip() or None
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO review (user_id, book_id, rating, content)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, book_id, rating, content),
        )
        conn.commit()
    flash("评价已提交")
    return redirect(url_for("book_detail", book_id=book_id))


if __name__ == "__main__":
    app.run(debug=True)