CREATE TABLE role (
  role_id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE "user" (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  role_id INT REFERENCES role(role_id) ON DELETE SET NULL
);

CREATE TABLE author (
  author_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE category (
  category_id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE book (
  book_id SERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  author_id INT REFERENCES author(author_id) ON DELETE SET NULL,
  category_id INT REFERENCES category(category_id) ON DELETE SET NULL,
  isbn VARCHAR(20) UNIQUE,
  stock INT NOT NULL DEFAULT 0
);

CREATE TABLE borrow (
  borrow_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES "user"(user_id) ON DELETE CASCADE,
  book_id INT REFERENCES book(book_id) ON DELETE CASCADE,
  borrowed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  due_at TIMESTAMP NOT NULL,
  returned_at TIMESTAMP
);

CREATE TABLE review (
  review_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES "user"(user_id) ON DELETE CASCADE,
  book_id INT REFERENCES book(book_id) ON DELETE CASCADE,
  rating INT CHECK (rating BETWEEN 1 AND 5),
  content TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO role(name) VALUES ('admin'), ('user');

INSERT INTO author(name) VALUES ('J. K. Rowling'), ('George Orwell');
INSERT INTO category(name) VALUES ('Fantasy'), ('Dystopia');

INSERT INTO book(title, author_id, category_id, isbn, stock)
VALUES
('Harry Potter and the Philosopher''s Stone', 1, 1, '9780747532699', 5),
('1984', 2, 2, '9780451524935', 3);

INSERT INTO "user"(username, email, role_id)
VALUES ('admin', 'admin@example.com', 1), ('alice', 'alice@example.com', 2);