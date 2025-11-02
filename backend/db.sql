PRAGMA foreign_keys = ON;


CREATE TABLE IF NOT EXISTS companies (
  id   INTEGER PRIMARY KEY AUTOINCREMENT, 
  name TEXT NOT NULL UNIQUE
);


CREATE TABLE IF NOT EXISTS accounts (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  email     TEXT NOT NULL UNIQUE,
  password  TEXT NOT NULL,
  name      TEXT,
  phone     TEXT,
  role      TEXT NOT NULL CHECK (role IN ('UserAdmin','CSR','PIN','PlatformManager')),
  status    TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','blocked')),
  company_id INTEGER,
  CHECK (
    (role = 'CSR' AND company_id IS NOT NULL) OR
    (role <> 'CSR' AND company_id IS NULL)
  ),
  FOREIGN KEY (company_id) REFERENCES companies(id)
);


CREATE TABLE IF NOT EXISTS volunteers (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT,
    email     TEXT,
    phone     TEXT,
    company_id INTEGER,   
    FOREIGN KEY (company_id) REFERENCES companies(id)
);



CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,      
    description TEXT
);


CREATE TABLE IF NOT EXISTS regions (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE
);


CREATE TABLE IF NOT EXISTS districts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id  INTEGER NOT NULL,
    name       TEXT NOT NULL,
    UNIQUE (region_id, name),
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    pin_id              INTEGER NOT NULL,  
    csr_id              INTEGER,           
    category_id         INTEGER NOT NULL,
    district_id         INTEGER NOT NULL,
    title               TEXT    NOT NULL,
    description         TEXT,
    start_at            TEXT,
    end_at              TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    volunteers          TEXT,
    view_count          INTEGER NOT NULL DEFAULT 0,
    feedback_rating     INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    feedback_comment    TEXT,
    feedback_created_at TEXT,

    FOREIGN KEY (pin_id) REFERENCES accounts(id)        ON DELETE RESTRICT,
    FOREIGN KEY (csr_id) REFERENCES accounts(id)        ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (district_id) REFERENCES districts(id)  ON DELETE RESTRICT
);


CREATE TABLE IF NOT EXISTS shortlist (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  csr_id     INTEGER NOT NULL,
  request_id INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (csr_id, request_id),
  FOREIGN KEY (csr_id)     REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS notifications (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id          INTEGER NOT NULL,               
  request_id       INTEGER,                        
  actor_id         INTEGER,                        
  type             TEXT NOT NULL,             
  message          TEXT,                          
  read_at          TEXT,                           
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY (user_id)    REFERENCES accounts(id)  ON DELETE CASCADE,
  FOREIGN KEY (actor_id)   REFERENCES accounts(id)  ON DELETE SET NULL,
  FOREIGN KEY (request_id) REFERENCES requests(id)  ON DELETE SET NULL
);


CREATE VIEW IF NOT EXISTS v_requests_status AS
SELECT
  r.*,
  CASE
    WHEN datetime('now') < datetime(r.start_at) AND r.csr_id IS NULL THEN 'pending'
    WHEN datetime('now') < datetime(r.start_at) AND r.csr_id IS NOT NULL THEN 'accepted'
    WHEN datetime('now') >= datetime(r.start_at) AND r.csr_id IS NOT NULL THEN 'completed'
    WHEN datetime('now') >= datetime(r.start_at) AND r.csr_id IS NULL THEN 'expired'
  END AS computed_status
FROM requests r;


CREATE VIEW IF NOT EXISTS v_requests AS
SELECT
    r.id,
    c.name   AS type,
    rg.name   AS region,
    d.name    AS district,
    r.title,
    r.description,
    v.computed_status AS status
FROM requests r
JOIN categories c ON r.category_id = c.id
JOIN districts  d ON r.district_id = d.id
JOIN regions   rg ON d.region_id = rg.id;

CREATE INDEX IF NOT EXISTS idx_districts_region     ON districts(region_id);
CREATE INDEX IF NOT EXISTS idx_requests_district    ON requests(district_id);
CREATE INDEX IF NOT EXISTS idx_requests_category    ON requests(category_id);
CREATE INDEX IF NOT EXISTS idx_requests_pin         ON requests(pin_id);
CREATE INDEX IF NOT EXISTS idx_requests_csr         ON requests(csr_id);
CREATE INDEX IF NOT EXISTS idx_requests_start_at    ON requests(start_at);
CREATE INDEX IF NOT EXISTS idx_requests_end_at      ON requests(end_at);
CREATE INDEX IF NOT EXISTS idx_shortlist_csr        ON shortlist(csr_id);
CREATE INDEX IF NOT EXISTS idx_shortlist_request    ON shortlist(request_id);
CREATE INDEX IF NOT EXISTS idx_requests_pin_startat ON requests(pin_id, start_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, read_at);

CREATE TRIGGER IF NOT EXISTS trg_shortlist_cleanup_on_assign
AFTER UPDATE OF csr_id ON requests
WHEN NEW.csr_id IS NOT NULL
BEGIN
  DELETE FROM shortlist
  WHERE request_id = NEW.id
    AND csr_id <> NEW.csr_id;
END;