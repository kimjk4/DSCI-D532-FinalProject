DROP TABLE IF EXISTS schedule_instances;
DROP TABLE IF EXISTS schedule_templates;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS activity_types;
DROP TABLE IF EXISTS providers;

CREATE TABLE providers (
  provider_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  initials VARCHAR(4) NOT NULL UNIQUE,
  role CHAR(2) NOT NULL CHECK (role IN ('S', 'NP'))
);

CREATE TABLE activity_types (
  activity_type_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  activity_name VARCHAR(50) NOT NULL,
  is_operating BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE locations (
  location_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  location_code VARCHAR(40) NOT NULL,
  location_name VARCHAR(100),
  activity_type_id INT UNSIGNED NOT NULL,
  FOREIGN KEY (activity_type_id)
    REFERENCES activity_types(activity_type_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE TABLE schedule_templates (
  template_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  provider_id        INT UNSIGNED NOT NULL,
  week_of_month      INT UNSIGNED NOT NULL CHECK (week_of_month BETWEEN 1 AND 5),
  day_of_week        INT UNSIGNED NOT NULL CHECK (day_of_week BETWEEN 1 AND 5),
  session            ENUM('AM','PM','FD') NOT NULL DEFAULT 'FD',
  location_id_odd    INT UNSIGNED NOT NULL,
  location_id_even   INT UNSIGNED DEFAULT NULL,
  details            TEXT DEFAULT NULL,

  FOREIGN KEY (provider_id)
      REFERENCES providers(provider_id)
      ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (location_id_odd)
      REFERENCES locations(location_id)
      ON UPDATE CASCADE ON DELETE RESTRICT,
  FOREIGN KEY (location_id_even)
      REFERENCES locations(location_id)
      ON UPDATE CASCADE ON DELETE RESTRICT,
  UNIQUE KEY uq_slot(provider_id, week_of_month, day_of_week, session)
);

CREATE TABLE schedule_instances (
  instance_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

  provider_id INT UNSIGNED NOT NULL,
  schedule_date DATE NOT NULL,
  session ENUM('AM', 'PM', 'FD') NOT NULL DEFAULT 'FD',
  location_id INT UNSIGNED NOT NULL,
  template_id INT UNSIGNED,
  generated_from_template INT NOT NULL DEFAULT 1,
  notes TEXT NULL,

  FOREIGN KEY (provider_id)
    REFERENCES providers(provider_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (location_id)
    REFERENCES locations(location_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  FOREIGN KEY (template_id)
    REFERENCES schedule_templates(template_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  UNIQUE KEY uq_assignment(provider_id, schedule_date, session)
);
