INSERT INTO users (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO guests 
  (name, email, telephone, address_1, address_2, city, county, postcode, modified, modified_by_id)
VALUES
  ("Alice Johnson", "alice.johnson@example.com", "+44 20 7123 4581", "67 Cherry St", "Apt 2A", "Liverpool", "Merseyside", "L1 1AA", "2024-05-30 12:59:24", 1),
  ("Chris Brown", "chris.brown@example.com", "+44 20 7123 4571", "202 Birch Ln", "Ste 9", "Glasgow", "Strathclyde", "G1 5AA", "2024-01-30 08:02:01", 1);

INSERT INTO room_types
  (type_name, base_price_per_night, amenities, photo, max_occupants, modified_by_id)
VALUES
  ("Superior Double", 130.00, "King-size bed, bath, sea views", "superior_room.jpg", 2, 1),
  ("Classic Double", 115.00, "King-size bed, shower, tea and coffee", "classic_double_room.jpg", 1, 1);

INSERT INTO reservation_status
  (status, description, bg_color)
VALUES
  ("Confirmed","Reservation has been confirmed by email.", "#c3f457"),
  ("Checked-in","Guest has checked into their room.", "");