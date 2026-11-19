-- Rename customer_email to billing_email and replace the free-form notes column
-- with internal_memo. SQLite cannot change these in place, so rebuild the table.
CREATE TABLE invoices_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    billing_email TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'sent', 'paid', 'void')),
    tax_rate_bps INTEGER NOT NULL DEFAULT 0,
    due_date TEXT NOT NULL,
    internal_memo TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO invoices_new
    (id, number, customer_name, billing_email, currency, status, tax_rate_bps, due_date, created_at)
SELECT id, number, customer_name, customer_email, currency, status, tax_rate_bps, due_date, created_at
FROM invoices;

DROP TABLE invoices;
ALTER TABLE invoices_new RENAME TO invoices;
