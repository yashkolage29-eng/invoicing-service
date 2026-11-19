CREATE INDEX idx_invoices_status_due ON invoices (status, due_date);
CREATE INDEX idx_line_items_invoice ON line_items (invoice_id);
