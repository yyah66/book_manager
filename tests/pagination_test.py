import datetime
import os
import re
import sys
import uuid
from contextlib import closing

import psycopg
from psycopg.rows import dict_row

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import config
from app import app

PER_PAGE = 5
BOOK_COUNT = 8
BORROW_COUNT = 6
BOOK_PAGES = (BOOK_COUNT + PER_PAGE - 1) // PER_PAGE


def open_conn():
    return psycopg.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        row_factory=dict_row,
    )


def seed_data():
    suffix = uuid.uuid4().hex[:8]
    book_prefix = f"Test Pagination {suffix}"
    author_name = f"Author {suffix}"
    category_name = f"Category {suffix}"
    user_name = f"pagination_user_{suffix}"
    with closing(open_conn()) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO author (name) VALUES (%s) RETURNING author_id",
            (author_name,),
        )
        author_id = cur.fetchone()["author_id"]
        cur.execute(
            "INSERT INTO category (name) VALUES (%s) RETURNING category_id",
            (category_name,),
        )
        category_id = cur.fetchone()["category_id"]
        cur.execute(
            'INSERT INTO "user" (username, email, role_id) VALUES (%s, %s, %s) RETURNING user_id',
            (user_name, f"{user_name}@example.com", None),
        )
        user_id = cur.fetchone()["user_id"]
        book_ids = []
        for idx in range(1, BOOK_COUNT + 1):
            title = f"{book_prefix} {idx}"
            isbn = f"{suffix}{idx:04d}"
            cur.execute(
                """
                INSERT INTO book (title, author_id, category_id, isbn, stock)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING book_id
                """,
                (title, author_id, category_id, isbn, 10),
            )
            book_ids.append(cur.fetchone()["book_id"])
        borrow_ids = []
        now = datetime.datetime.now()
        for idx in range(BORROW_COUNT):
            due_at = now + datetime.timedelta(days=idx + 7)
            cur.execute(
                """
                INSERT INTO borrow (user_id, book_id, due_at)
                VALUES (%s, %s, %s)
                RETURNING borrow_id
                """,
                (user_id, book_ids[idx % len(book_ids)], due_at),
            )
            borrow_ids.append(cur.fetchone()["borrow_id"])
        conn.commit()
    return {
        "author_id": author_id,
        "category_id": category_id,
        "user_id": user_id,
        "book_ids": book_ids,
        "borrow_ids": borrow_ids,
        "book_prefix": book_prefix,
        "user_name": user_name,
    }


def cleanup(data):
    with closing(open_conn()) as conn, conn.cursor() as cur:
        for borrow_id in data["borrow_ids"]:
            cur.execute("DELETE FROM borrow WHERE borrow_id = %s", (borrow_id,))
        for book_id in data["book_ids"]:
            cur.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
        cur.execute(
            'DELETE FROM "user" WHERE user_id = %s',
            (data["user_id"],),
        )
        cur.execute(
            "DELETE FROM author WHERE author_id = %s",
            (data["author_id"],),
        )
        cur.execute(
            "DELETE FROM category WHERE category_id = %s",
            (data["category_id"],),
        )
        conn.commit()


def extract_titles(html, prefix):
    pattern = re.compile(rf">{re.escape(prefix)} (\d+)</a>")
    matches = pattern.findall(html)
    return [f"{prefix} {m}" for m in matches]


def check_book_list(client, data):
    resp = client.get("/", query_string={"q": data["book_prefix"], "page": 1})
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    titles = extract_titles(html, data["book_prefix"])
    expected_first_page = [
        f"{data['book_prefix']} {idx}"
        for idx in range(BOOK_COUNT, BOOK_COUNT - PER_PAGE, -1)
        if idx > 0
    ]
    assert titles == expected_first_page
    assert f"第 1 / {BOOK_PAGES} 页" in html
    resp = client.get("/", query_string={"q": data["book_prefix"], "page": 2})
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    titles = extract_titles(html, data["book_prefix"])
    expected_second_page = [
        f"{data['book_prefix']} {idx}"
        for idx in range(BOOK_COUNT - PER_PAGE, 0, -1)
    ]
    assert titles == expected_second_page
    assert f"第 2 / {BOOK_PAGES} 页" in html


def check_borrow_list(client, data):
    resp = client.get("/borrows")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert data["user_name"] in html
    assert str(data["borrow_ids"][-1]) in html
    assert "第 1 /" in html and "页" in html
    if BORROW_COUNT > PER_PAGE:
        resp = client.get("/borrows", query_string={"page": 2})
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert str(data["borrow_ids"][0]) in html
        assert "第 2 /" in html and "页" in html


def main():
    data = seed_data()
    try:
        app.config["TESTING"] = True
        with app.test_client() as client:
            check_book_list(client, data)
            check_borrow_list(client, data)
    finally:
        cleanup(data)
    print("Pagination checks passed.")


if __name__ == "__main__":
    main()
