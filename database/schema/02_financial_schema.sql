
USE upi_fraud_system;

-- ==========================================
-- 7. LEDGER ACCOUNTS
-- ==========================================

CREATE TABLE ledger_accounts (
    account_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    merchant_id BIGINT NULL,
    account_name VARCHAR(150) NOT NULL,
    account_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ledger_account_merchant
        FOREIGN KEY (merchant_id)
        REFERENCES merchants(merchant_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_ledger_account_type
        CHECK (
            account_type IN (
                'CUSTOMER',
                'MERCHANT',
                'PLATFORM',
                'FEE',
                'SETTLEMENT'
            )
        ),

    CONSTRAINT chk_ledger_account_status
        CHECK (status IN ('ACTIVE', 'INACTIVE'))
) ENGINE=InnoDB;


-- ==========================================
-- 8. SETTLEMENTS
-- ==========================================

CREATE TABLE settlements (
    settlement_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    merchant_id BIGINT NOT NULL,
    settlement_reference VARCHAR(100) NOT NULL UNIQUE,

    gross_amount DECIMAL(12,2) NOT NULL,
    adjustment_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    net_amount DECIMAL(12,2) NOT NULL,

    settlement_status VARCHAR(20) NOT NULL DEFAULT 'CREATED',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    settled_at DATETIME NULL,

    CONSTRAINT fk_settlement_merchant
        FOREIGN KEY (merchant_id)
        REFERENCES merchants(merchant_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_settlement_amounts
        CHECK (
            gross_amount >= 0
            AND net_amount >= 0
            AND net_amount = gross_amount + adjustment_amount
        ),

    CONSTRAINT chk_settlement_status
        CHECK (
            settlement_status IN (
                'CREATED',
                'PROCESSING',
                'SETTLED',
                'FAILED'
            )
        )
) ENGINE=InnoDB;


-- ==========================================
-- 9. LEDGER TRANSACTIONS
-- ==========================================

CREATE TABLE ledger_transactions (
    ledger_transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    transaction_id BIGINT NULL,
    settlement_id BIGINT NULL,

    posting_type VARCHAR(30) NOT NULL,
    posting_reference VARCHAR(100) NOT NULL UNIQUE,

    posted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ledger_transaction_payment
        FOREIGN KEY (transaction_id)
        REFERENCES payment_transactions(transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_ledger_transaction_settlement
        FOREIGN KEY (settlement_id)
        REFERENCES settlements(settlement_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_ledger_source
        CHECK (
            (transaction_id IS NOT NULL AND settlement_id IS NULL)
            OR
            (transaction_id IS NULL AND settlement_id IS NOT NULL)
        ),

    CONSTRAINT chk_ledger_posting_type
        CHECK (
            posting_type IN (
                'PAYMENT',
                'REFUND',
                'SETTLEMENT',
                'FEE'
            )
        )
) ENGINE=InnoDB;


-- ==========================================
-- 10. LEDGER ENTRIES
-- ==========================================

CREATE TABLE ledger_entries (
    ledger_entry_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    ledger_transaction_id BIGINT NOT NULL,
    account_id BIGINT NOT NULL,

    entry_type VARCHAR(10) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ledger_entry_transaction
        FOREIGN KEY (ledger_transaction_id)
        REFERENCES ledger_transactions(ledger_transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_ledger_entry_account
        FOREIGN KEY (account_id)
        REFERENCES ledger_accounts(account_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_ledger_entry_type
        CHECK (entry_type IN ('DEBIT', 'CREDIT')),

    CONSTRAINT chk_ledger_entry_amount
        CHECK (amount > 0)
) ENGINE=InnoDB;


-- ==========================================
-- 11. SETTLEMENT ITEMS
-- ==========================================

CREATE TABLE settlement_items (
    settlement_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    settlement_id BIGINT NOT NULL,
    transaction_id BIGINT NOT NULL,

    allocated_amount DECIMAL(12,2) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_settlement_item_settlement
        FOREIGN KEY (settlement_id)
        REFERENCES settlements(settlement_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_settlement_item_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES payment_transactions(transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_settlement_transaction
        UNIQUE (settlement_id, transaction_id),

    CONSTRAINT chk_allocated_amount
        CHECK (allocated_amount > 0)
) ENGINE=InnoDB;


-- ==========================================
-- 12. RECONCILIATION RUNS
-- ==========================================

CREATE TABLE reconciliation_runs (
    reconciliation_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    settlement_id BIGINT NOT NULL,

    expected_amount DECIMAL(12,2) NOT NULL,
    actual_amount DECIMAL(12,2) NOT NULL,
    difference_amount DECIMAL(12,2) NOT NULL,

    reconciliation_status VARCHAR(20) NOT NULL,

    executed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reconciliation_settlement
        FOREIGN KEY (settlement_id)
        REFERENCES settlements(settlement_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_reconciliation_amounts
        CHECK (
            expected_amount >= 0
            AND actual_amount >= 0
            AND difference_amount = actual_amount - expected_amount
        ),

    CONSTRAINT chk_reconciliation_status
        CHECK (
            reconciliation_status IN (
                'MATCHED',
                'MISMATCHED',
                'PENDING'
            )
        )
) ENGINE=InnoDB;


-- ==========================================
-- 13. RECONCILIATION EXCEPTIONS
-- ==========================================

CREATE TABLE reconciliation_exceptions (
    exception_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    reconciliation_id BIGINT NOT NULL,
    transaction_id BIGINT NULL,

    exception_type VARCHAR(50) NOT NULL,
    discrepancy_amount DECIMAL(12,2) NOT NULL,

    resolution_status VARCHAR(20) NOT NULL DEFAULT 'OPEN',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,

    CONSTRAINT fk_exception_reconciliation
        FOREIGN KEY (reconciliation_id)
        REFERENCES reconciliation_runs(reconciliation_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_exception_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES payment_transactions(transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_exception_status
        CHECK (
            resolution_status IN (
                'OPEN',
                'INVESTIGATING',
                'RESOLVED'
            )
        )
) ENGINE=InnoDB;
