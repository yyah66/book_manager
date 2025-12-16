# 图书管理系统（openGauss + Flask）

## 快速开始（Windows cmd.exe）

py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

gsql -h 127.0.0.1 -p 5432 -U gaussdb -d book_manager -W -f e:\book_manager\database.sql

set FLASK_APP=app.py
set DB_HOST=127.0.0.1
set DB_PORT=5432
set DB_NAME=book_manager
set DB_USER=gaussdb
set DB_PASSWORD=your_password

py app.py
