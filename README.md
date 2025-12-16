# 图书管理系统（openGauss + Flask）

## 1. 环境要求

- Windows 10/11
- Python 3.11（或 3.12，3.13 暂无 psycopg 官方 wheel）
- Docker Desktop（用于启动 openGauss 容器）或本地已安装的 openGauss
- Git（可选，用于版本控制）

## 2. 一次性初始化（cmd.exe）

```bat
REM 进入项目目录

REM 创建并激活虚拟环境
py -3.11 -m venv .venv
\.venv\Scripts\activate

REM 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.1 启动 openGauss 容器并导入建表脚本

```bat
REM 拉取并启动 openGauss（密码可自定义）
docker pull enmotech/opengauss:latest
docker run --name my-opengauss ^
	-p 5432:5432 ^
	-e GS_PASSWORD=OpenGauss@123 ^
	-d enmotech/opengauss:latest

REM 拷贝建表脚本到容器
docker cp e:\book_manager\database.sql my-opengauss:/tmp/database.sql

REM 进入容器导入脚本
docker exec -it my-opengauss bash
su - omm
export PATH=/usr/local/opengauss/bin:$PATH
gsql -d postgres -p 5432 -U gaussdb -W OpenGauss@123 <<'SQL'
CREATE DATABASE book_manager;
\c book_manager
\i /tmp/database.sql
SQL
exit
exit
```

> 如果使用已有的 openGauss，可在其终端中直接运行 `gsql -d postgres -U gaussdb` 并执行 `\i /path/to/database.sql`。

## 3. 启动应用

```bat
进入文件所在目录
激活对应虚拟环境
set FLASK_APP=app.py
set DB_HOST=127.0.0.1
set DB_PORT=5432
set DB_NAME=book_manager
set DB_USER=gaussdb
set DB_PASSWORD=OpenGauss@123

py app.py
```

在另一个终端或同一终端追加执行：

```bat
start http://127.0.0.1:5000/
```

## 4. 功能简介

- 图书列表：搜索、查看、增删改、库存管理
- 作者 / 分类：独立维护，一键新增
- 用户管理：新增借阅人，借阅前确保存在用户记录
- 借阅 / 归还：校验用户与库存，自动更新状态
- 书评：用户评分与评论展示

## 5. 常见问题

- **psycopg 安装失败**：确认 Python ≤ 3.12；必要时删除 `.venv` 后重新创建。
- **gsql 命令不存在**：容器内切换到 `omm` 用户并执行 `export PATH=/usr/local/opengauss/bin:$PATH`。
- **借阅提示用户不存在**：先在“用户”页面创建用户，再在图书详情页借阅。
- **端口冲突**：调整 `docker run` 中 `-p` 的宿主端口，并同步修改环境变量 `DB_PORT`。
