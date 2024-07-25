DROP TABLE IF EXISTS availabilities;
CREATE TABLE IF NOT EXISTS availabilities (
    id SERIAL PRIMARY KEY,
    apartment VARCHAR(100) NOT NULL,
    plan VARCHAR(50),
    unit VARCHAR(50) NOT NULL,
    bedrooms VARCHAR(100) NOT NULL,
    beds FLOAT NOT NULL,
    baths FLOAT NOT NULL,
    sqft FLOAT NOT NULL,
    rent FLOAT,
    available_date DATE NOT NULL,
    retrieved TIMESTAMP NOT NULL--DEFAULT CURRENT_TIMESTAMP
);