DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS guests;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

-- Create default admin account with password 'dev'
INSERT INTO users (username, password)
  VALUES ("admin","scrypt:32768:8:1$qJPjpVKh4Fral5mv$b75a4aed584520875c127fa655a42cdd578e5614600e7b7be23479db6ca50f945ede38ff38da8d8aea72d06e3094cfece2e7d713d2f4b31f8a47c090828f2842" );

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
  notes TEXT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  modified_by_id INTEGER NOT NULL,
  FOREIGN KEY (modified_by_id) REFERENCES users (id)
);

-- Insert dummy guest data
INSERT INTO guests 
  (name, email, telephone, address_1, address_2, city, county, postcode, modified_by_id)
VALUES
  ("John Doe", "john.doe@example.com", "+44 20 7123 4567", "123 Elm St", "Apt 4B", "London", "Greater London", "W1A 1AA", 1),
  ("Jane Smith", "jane.smith@example.com", "+44 20 7123 4568", "456 Oak Ave", "Suite 300", "Manchester", "Greater Manchester", "M1 2AA", 1),
  ("Michael Johnson", "michael.johnson@example.com", "+44 20 7123 4569", "789 Pine Rd", "Unit 12", "Birmingham", "West Midlands", "B1 3AA", 1),
  ("Emily Davis", "emily.davis@example.com", "+44 20 7123 4570", "101 Maple Dr", "Floor 5", "Leeds", "West Yorkshire", "LS1 4AA", 1),
  ("Chris Brown", "chris.brown@example.com", "+44 20 7123 4571", "202 Birch Ln", "Ste 9", "Glasgow", "Strathclyde", "G1 5AA", 1),
  ("Amanda Wilson", "amanda.wilson@example.com", "+44 20 7123 4572", "303 Cedar Blvd", "Rm 7", "Edinburgh", "Lothian", "EH1 6AA", 1),
  ("Robert Miller", "robert.miller@example.com", "+44 20 7123 4573", "404 Willow St", "Bldg 8", "Cardiff", "South Glamorgan", "CF1 7AA", 1),
  ("Sarah Taylor", "sarah.taylor@example.com", "+44 20 7123 4574", "505 Redwood Way", "Fl 3", "Belfast", "County Antrim", "BT1 8AA", 1);
