INSERT INTO customers (id, name, city, signup_date) VALUES
    (1, 'Alice', 'Seattle',  '2024-01-15'),
    (2, 'Bob',   'Portland', '2024-02-20'),
    (3, 'Carol', 'Seattle',  '2024-03-05'),
    (4, 'Dave',  'Austin',   '2024-03-18'),
    (5, 'Eve',   'Seattle',  '2024-04-02');

INSERT INTO products (id, name, category, price) VALUES
    (1, 'Widget',   'Hardware',    9.99),
    (2, 'Gadget',   'Hardware',   19.99),
    (3, 'Notebook', 'Office',      4.50),
    (4, 'Pen',      'Office',      1.25),
    (5, 'Monitor',  'Electronics', 199.00),
    (6, 'Stapler',  'Office',      7.75);

INSERT INTO orders (id, customer_id, order_date, status) VALUES
    (1, 1, '2024-03-01', 'completed'),
    (2, 1, '2024-03-15', 'completed'),
    (3, 2, '2024-03-20', 'cancelled'),
    (4, 3, '2024-04-01', 'completed'),
    (5, 4, '2024-04-10', 'pending'),
    (6, 5, '2024-04-15', 'completed');

INSERT INTO order_items (order_id, product_id, quantity) VALUES
    (1, 1, 2),
    (1, 3, 1),
    (2, 5, 1),
    (3, 2, 3),
    (4, 1, 1),
    (4, 4, 5),
    (5, 5, 2),
    (6, 3, 10);
