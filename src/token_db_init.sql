CREATE TABLE IF NOT EXISTS used_tokens (
    token_id TEXT PRIMARY KEY,
    shop_id TEXT NOT NULL,
    issued_date DATE,
    used BOOLEAN DEFAULT 0,
    used_at DATETIME
);
