DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS guests;
DROP TABLE IF EXISTS room_types;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS reservation_status;
DROP TABLE IF EXISTS special_offers;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS invoice_items;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS join_guests_reservations;
DROP TABLE IF EXISTS join_rooms_reservations;


CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE guests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  telephone TEXT NOT NULL,
  address_1 TEXT NOT NULL,
  address_2 TEXT,
  city TEXT NOT NULL,
  county TEXT NOT NULL,
  postcode TEXT NOT NULL,
  guest_notes TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (modified_by_id) REFERENCES users (id)
);

CREATE TABLE room_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type_name TEXT NOT NULL,
  base_price_per_night REAL NOT NULL,
  amenities TEXT NOT NULL,
  photo TEXT NOT NULL,
  max_occupants INTEGER NOT NULL,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (modified_by_id) REFERENCES users (id)
);

CREATE TABLE rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  room_number INTEGER NOT NULL,
  room_type INTEGER NOT NULL,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (modified_by_id) REFERENCES users (id),
  FOREIGN KEY (room_type) REFERENCES room_types (id)
);

CREATE TABLE reservations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  number_of_guests INTEGER NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  total_room_base_price REAL NOT NULL,
  special_offer_applied TEXT,
  special_offer_discount REAL NOT NULL DEFAULT 0,
  reservation_notes TEXT,
  status_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (modified_by_id) REFERENCES users (id),
  FOREIGN KEY (status_id) REFERENCES reservation_status (id)
);

CREATE TABLE reservation_status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  status TEXT NOT NULL,
  description TEXT,
  bg_color TEXT
);

CREATE TABLE special_offers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  room_type INTEGER NOT NULL,
  price_per_night REAL NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  is_enabled INTEGER DEFAULT 0,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (modified_by_id) REFERENCES users (id),
  FOREIGN KEY (room_type) REFERENCES room_types (id)
);

CREATE TABLE invoices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reservation_id INTEGER NOT NULL,
  amount_paid REAL NOT NULL DEFAULT 0,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (reservation_id) REFERENCES reservations (id)
);

CREATE TABLE invoice_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id INTEGER NOT NULL,
  item_description TEXT NOT NULL,
  is_room INTEGER DEFAULT 0,
  quantity INTEGER NOT NULL,
  price REAL NOT NULL,
  total REAL NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (invoice_id) REFERENCES invoices (id)
);

CREATE TABLE payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (invoice_id) REFERENCES invoices (id)
);

CREATE TABLE join_guests_reservations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guest_id INTEGER NOT NULL,
  reservation_id INTEGER NOT NULL,
  FOREIGN KEY (guest_id) REFERENCES guests (id),
  FOREIGN KEY (reservation_id) REFERENCES reservations (id)
);

CREATE TABLE join_rooms_reservations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id INTEGER NOT NULL,
  reservation_id INTEGER NOT NULL,
  FOREIGN KEY (room_id) REFERENCES rooms (id),
  FOREIGN KEY (reservation_id) REFERENCES reservations (id)
);
