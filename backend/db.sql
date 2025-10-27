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
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pin_id     INTEGER NOT NULL,  
    -- The user ID of the PIN (Person-In-Need) who created the request.
    csr_id     INTEGER,           
    -- The user ID of the CSR (Corporate Social Responsibility) representative
    category_id     INTEGER NOT NULL,
    district_id     INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT,
    status          TEXT    NOT NULL CHECK (status IN ('pending','accepted','completed','expired')),
    start_at        TEXT,
    end_at          TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    volunteers      TEXT,

    CHECK (
      (
        status IN ('pending','expired')
        AND csr_id IS NULL
        AND (volunteers IS NULL OR JSON_ARRAY_LENGTH(volunteers) = 0)
      )
      OR
      (
        status IN ('accepted','completed')
        AND csr_id IS NOT NULL
        AND JSON_ARRAY_LENGTH(volunteers) >= 1
      )
    )

    FOREIGN KEY (pin_id) REFERENCES accounts(id)        ON DELETE RESTRICT,
    FOREIGN KEY (csr_id) REFERENCES accounts(id)        ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (district_id) REFERENCES districts(id)  ON DELETE RESTRICT
);

CREATE VIEW IF NOT EXISTS v_requests AS
SELECT
    r.id,
    c.name   AS type,
    rg.name   AS region,
    d.name    AS district,
    r.title,
    r.description,
    r.status
FROM requests r
JOIN categories c ON r.category_id = c.id
JOIN districts  d ON r.district_id = d.id
JOIN regions   rg ON d.region_id = rg.id;


CREATE INDEX IF NOT EXISTS idx_districts_region     ON districts(region_id);
CREATE INDEX IF NOT EXISTS idx_requests_district    ON requests(district_id);
CREATE INDEX IF NOT EXISTS idx_requests_category    ON requests(category_id);
CREATE INDEX IF NOT EXISTS idx_requests_status      ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_pin         ON requests(pin_id);
CREATE INDEX IF NOT EXISTS idx_requests_csr         ON requests(csr_id);
CREATE INDEX IF NOT EXISTS idx_requests_start_at    ON requests(start_at);
CREATE INDEX IF NOT EXISTS idx_requests_end_at      ON requests(end_at);