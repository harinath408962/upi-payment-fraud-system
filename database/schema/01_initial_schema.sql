
USE upi_fraud_system;

-- ==========================================
-- 1. MERCHANT
-- ==========================================

CREATE TABLE merchants (
    merchant_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    merchant_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL,
    business_type VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_merchant_status
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED'))
) ENGINE=InnoDB;


-- ==========================================
-- 2. CUSTOMER
-- ==========================================

CREATE TABLE customers (
    customer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(15) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


-- ==========================================
-- 3. PAYMENT METHOD
-- ==========================================

CREATE TABLE payment_methods (
    payment_method_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    method_type VARCHAR(30) NOT NULL,
    payment_token VARCHAR(255) NOT NULL UNIQUE,
    display_identifier VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_method_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_payment_method_type
        CHECK (method_type IN ('UPI', 'CARD', 'WALLET')),

    CONSTRAINT chk_payment_method_status
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'BLOCKED'))
) ENGINE=InnoDB;


-- ==========================================
-- 4. PAYMENT TRANSACTIONS
-- ==========================================

CREATE TABLE payment_transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    merchant_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    payment_method_id BIGINT NOT NULL,

    idempotency_key VARCHAR(100) NOT NULL,
    request_hash CHAR(64) NOT NULL,

    amount DECIMAL(12,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'INR',

    transaction_status VARCHAR(20) NOT NULL DEFAULT 'CREATED',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_transaction_merchant
        FOREIGN KEY (merchant_id)
        REFERENCES merchants(merchant_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_transaction_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_transaction_payment_method
        FOREIGN KEY (payment_method_id)
        REFERENCES payment_methods(payment_method_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_merchant_idempotency
        UNIQUE (merchant_id, idempotency_key),

    CONSTRAINT chk_transaction_amount
        CHECK (amount > 0),

    CONSTRAINT chk_transaction_status
        CHECK (
            transaction_status IN (
                'CREATED',
                'PENDING',
                'SUCCESS',
                'FAILED',
                'CANCELLED'
            )
        )
) ENGINE=InnoDB;


-- ==========================================
-- 5. PAYMENT ATTEMPTS
-- ==========================================

CREATE TABLE payment_attempts (
    payment_attempt_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    attempt_number INT NOT NULL,

    provider_reference VARCHAR(100) UNIQUE,
    provider_response JSON,

    attempted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_at DATETIME,

    CONSTRAINT fk_attempt_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES payment_transactions(transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_transaction_attempt
        UNIQUE (transaction_id, attempt_number),

    CONSTRAINT chk_attempt_number
        CHECK (attempt_number > 0)
) ENGINE=InnoDB;


-- ==========================================
-- 6. RETRY ATTEMPTS
-- ==========================================

CREATE TABLE retry_attempts (
    retry_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    retry_number INT NOT NULL,

    retry_source VARCHAR(30) NOT NULL,
    retry_reason VARCHAR(255),
    retry_status VARCHAR(20) NOT NULL,

    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_retry_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES payment_transactions(transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_transaction_retry
        UNIQUE (transaction_id, retry_number),

    CONSTRAINT chk_retry_number
        CHECK (retry_number > 0),

    CONSTRAINT chk_retry_status
        CHECK (
            retry_status IN (
                'REQUESTED',
                'COMPLETED',
                'FAILED',
                'SKIPPED'
            )
        )
) ENGINE=InnoDB;
