-- Olist Brazilian E-commerce dataset (public, Kaggle: olistbr/brazilian-ecommerce).
-- One table per CSV file, column names kept as in the CSVs (except the typo fix in
-- products) so the Kaggle data dictionary still applies.
--
-- Conventions used below:
-- * Separate `olist` schema: the read-only SQL tool (Milestone 5) will be granted access
--   to this schema only, never to RAG tables or schema_migrations.
-- * Timestamps are `timestamp` WITHOUT time zone: the CSVs carry no offset; the values are
--   Brazilian local time as published. `timestamptz` would silently treat them as the
--   session time zone (UTC in the container) and shift them.
-- * Zip code prefixes are `text`: they are identifiers with meaningful leading zeros ("01037").
-- * Money is `numeric(10, 2)`: exact decimal arithmetic, no float rounding in sums.
-- * Postgres does not index foreign-key columns automatically; the indexes below cover
--   the joins and filters metrics queries will use.

CREATE SCHEMA olist;

CREATE TABLE olist.product_category_translation (
    product_category_name         text PRIMARY KEY,
    product_category_name_english text NOT NULL
);

CREATE TABLE olist.customers (
    -- customer_id is created per order; customer_unique_id identifies the same person
    -- across orders (needed for repeat-purchase and retention metrics).
    customer_id              text PRIMARY KEY,
    customer_unique_id       text NOT NULL,
    customer_zip_code_prefix text NOT NULL,
    customer_city            text NOT NULL,
    customer_state           char(2) NOT NULL
);
CREATE INDEX ON olist.customers (customer_unique_id);

CREATE TABLE olist.sellers (
    seller_id              text PRIMARY KEY,
    seller_zip_code_prefix text NOT NULL,
    seller_city            text NOT NULL,
    seller_state           char(2) NOT NULL
);

CREATE TABLE olist.products (
    product_id                 text PRIMARY KEY,
    -- Nullable, and no FK to product_category_translation: some products have no category,
    -- and a few category names are missing from the translation file.
    product_category_name      text,
    -- The CSV headers misspell "length" as "lenght"; the loader maps them to these names.
    product_name_length        integer,
    product_description_length integer,
    product_photos_qty         integer,
    product_weight_g           integer,
    product_length_cm          integer,
    product_height_cm          integer,
    product_width_cm           integer
);

CREATE TABLE olist.orders (
    order_id                      text PRIMARY KEY,
    customer_id                   text NOT NULL REFERENCES olist.customers,
    order_status                  text NOT NULL,
    order_purchase_timestamp      timestamp NOT NULL,
    -- Nullable: not every order reaches every stage (canceled, unavailable, in transit).
    order_approved_at             timestamp,
    order_delivered_carrier_date  timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date timestamp NOT NULL
);
CREATE INDEX ON olist.orders (customer_id);
CREATE INDEX ON olist.orders (order_purchase_timestamp);

CREATE TABLE olist.order_items (
    order_id            text NOT NULL REFERENCES olist.orders,
    -- Position of the item within the order (1, 2, ...). There is no quantity column:
    -- buying 2 of the same product produces 2 rows.
    order_item_id       integer NOT NULL,
    product_id          text NOT NULL REFERENCES olist.products,
    seller_id           text NOT NULL REFERENCES olist.sellers,
    shipping_limit_date timestamp NOT NULL,
    price               numeric(10, 2) NOT NULL,
    freight_value       numeric(10, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);
CREATE INDEX ON olist.order_items (product_id);
CREATE INDEX ON olist.order_items (seller_id);

CREATE TABLE olist.order_payments (
    order_id             text NOT NULL REFERENCES olist.orders,
    -- An order can be paid with several methods (e.g. voucher + credit card).
    payment_sequential   integer NOT NULL,
    payment_type         text NOT NULL,
    payment_installments integer NOT NULL,
    payment_value        numeric(10, 2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE olist.order_reviews (
    -- review_id alone is NOT unique in the dataset: the same review can be attached to
    -- several orders. The pair (review_id, order_id) is unique.
    review_id               text NOT NULL,
    order_id                text NOT NULL REFERENCES olist.orders,
    review_score            smallint NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title    text,
    review_comment_message  text,
    review_creation_date    timestamp NOT NULL,
    review_answer_timestamp timestamp NOT NULL,
    PRIMARY KEY (review_id, order_id)
);
CREATE INDEX ON olist.order_reviews (order_id);

CREATE TABLE olist.geolocation (
    -- The file has no natural key (many rows per zip prefix), so we add a surrogate one.
    -- No FKs from customers/sellers: not every zip prefix they use appears here.
    id                          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    geolocation_zip_code_prefix text NOT NULL,
    geolocation_lat             double precision NOT NULL,
    geolocation_lng             double precision NOT NULL,
    geolocation_city            text NOT NULL,
    geolocation_state           char(2) NOT NULL
);
CREATE INDEX ON olist.geolocation (geolocation_zip_code_prefix);
