
USE upi_fraud_system;

-- ==========================================
-- 14. TRANSACTIONAL OUTBOX EVENTS
-- ==========================================

CREATE TABLE outbox_events (
    outbox_event_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    transaction_id BIGINT NOT NULL,

    event_type VARCHAR(100) NOT NULL,
    payload JSON NOT NULL,

    delivery_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    retry_count INT NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME NULL,

    CONSTRAINT fk_outbox_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES payment_transactions(transaction_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_outbox_delivery_status
        CHECK (
            delivery_status IN (
                'PENDING',
                'PROCESSING',
                'DELIVERED',
                'FAILED'
            )
        ),

    CONSTRAINT chk_outbox_retry_count
        CHECK (retry_count >= 0),

    INDEX idx_outbox_delivery (delivery_status, created_at)
) ENGINE=InnoDB;
