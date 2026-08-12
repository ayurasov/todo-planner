CREATE TABLE departments (
    id VARCHAR(36) PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE manager_departments (
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id VARCHAR(36) NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, department_id)
);

ALTER TABLE users ADD COLUMN department_id VARCHAR(36) REFERENCES departments(id) ON DELETE SET NULL;
ALTER TABLE lists ADD COLUMN department_id VARCHAR(36) REFERENCES departments(id) ON DELETE SET NULL;
ALTER TABLE meetings ADD COLUMN department_id VARCHAR(36) REFERENCES departments(id) ON DELETE SET NULL;
