-- Create default admin account with password 'dev'
INSERT INTO users (username, password)
  VALUES ("admin","scrypt:32768:8:1$qJPjpVKh4Fral5mv$b75a4aed584520875c127fa655a42cdd578e5614600e7b7be23479db6ca50f945ede38ff38da8d8aea72d06e3094cfece2e7d713d2f4b31f8a47c090828f2842" )
;

-- Insert room_types
INSERT INTO room_types
  (type_name, base_price_per_night, amenities, photo, max_occupants, modified_by_id)
VALUES
  ("Four Poster Nest", 145.0, "King-size bed, shower, bath", "four_poster_nest.jpg", 2, 1),
  ("Superior Double", 130.0, "King-size bed, shower, bath", "superior_room.jpg", 2, 1),
  ("Classic Double", 115.0, "King-size bed, shower, bath", "classic_double_room.jpg", 2, 1)
;

-- Insert rooms
INSERT INTO rooms
  (room_number, room_type, modified_by_id)
VALUES
  (1, 2, 1),
  (2, 1, 1),
  (3, 2, 1),
  (6, 3, 1),
  (7, 2, 1),
  (8, 3, 1),
  (9, 2, 1)
;

-- Insert reservation status
INSERT INTO reservation_status
  (status, description, bg_color)
VALUES
  ("Pending", "Reservation is not confirmed", "#cae6f6"),
  ("Confirmed","Reservation has been confirmed by email.", "#c3f457"),
  ("Checked-in","Guest has checked into their room.", "#f8e45c"),
  ("Paid in Full","Reservation invoice has been paid.", "#34c4d9"),
  ("Cancelled","Reservation has been cancelled.", "#f66151")
;

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
  ("Sarah Taylor", "sarah.taylor@example.com", "+44 20 7123 4574", "505 Redwood Way", "Fl 3", "Belfast", "County Antrim", "BT1 8AA", 1)
;

-- Insert dummy reservations
INSERT INTO reservations
  (start_date, end_date, total_room_base_price, special_offer_applied, special_offer_discount, number_of_guests, status_id, modified_by_id)
VALUES
  ("2024-09-17","2024-09-20",390.0,"",0,2,2,1),
  ("2024-08-20","2024-08-25",725.0,"125 discount",125,2,4,1),
  ("2024-09-08","2024-09-12",520.0,"",0,2,3,1),
  ("2024-09-01","2024-09-05",460.0,"",0,2,2,1),
  ("2024-09-03","2024-09-07",520.0,"",0,2,2,1),
  ("2024-09-10","2024-09-14",460.0,"",0,2,2,1),
  ("2024-09-19","2024-09-23",520.0,"",0,2,2,1),
  ("2024-09-12","2024-09-19",1015.0,"",0,2,1,1),
  ("2024-09-08","2024-09-12",520.0,"",0,2,3,1)
;

INSERT INTO special_offers
  (title, room_type, price_per_night, start_date, end_date, is_enabled, modified_by_id)
VALUES
  ("August 2024 - Superior Double", 2, 120, "2024-08-01", "2024-08-31", 1, 1),
  ("August 2024 - Four Poster", 1, 100, "2024-08-01", "2024-08-31", 1, 1)
;

INSERT INTO invoices
  (reservation_id, amount_paid, modified_by_id)
VALUES
  (2, 0, 1),
  (1, 390, 1)
;

INSERT INTO invoice_items
  (invoice_id, item_description, is_room, quantity, price, total, modified_by_id)
VALUES
  (2, "Superior Double", 1, 3, 130.0, 390.0, 1),
  (2, "Dinner", 0, 2, 25.0, 50.0, 1),
  (1, "Four Poster Nest", 1, 5, 145.0, 725.0, 1),
  (1, "Dinner", 0, 2, 25.0, 50.0, 1),
  (1, "Drinks", 0, 4, 2.5, 10.0, 1)
;

INSERT INTO payments
  (invoice_id, amount, modified_by_id)
VALUES
  (2,390,1)
;

INSERT INTO join_guests_reservations
  (guest_id, reservation_id)
VALUES
  (5, 1),
  (4, 2),
  (2, 3),
  (8, 4),
  (4, 5),
  (7, 6),
  (3, 7),
  (6, 8),
  (1, 9)
;

INSERT INTO join_rooms_reservations
  (room_id, reservation_id)
VALUES
  (1, 1),
  (2, 2),
  (3, 3),
  (4, 4),
  (5, 5),
  (6, 6),
  (3, 7),
  (2, 8),
  (7, 9)
;
