# Inventory Concurrency Management System

A robust **FastAPI** application designed to demonstrate and compare **Pessimistic** and **Optimistic** locking strategies in a high-contention multi-tenant environment. This project ensures data integrity, prevents overselling, and manages concurrent database updates using **PostgreSQL**.

## 🚀 Key Features

* **Pessimistic Locking**: Utilizes `SELECT ... FOR UPDATE` to lock database rows at the engine level, preventing other transactions from modifying the record until the lock is released.
* **Optimistic Locking**: Implements a version-based update strategy with a **3-retry mechanism** and **exponential backoff** to handle version mismatches under load.
* **Real-time Monitoring**: Includes a dedicated shell script to monitor PostgreSQL lock states (`pg_locks`) during execution.
* **Data Integrity**: Enforces a PostgreSQL `CHECK (stock >= 0)` constraint to prevent negative inventory.

---

## 🛠️ Tech Stack

* **Framework**: FastAPI (Python 3.12+)
* **Database**: PostgreSQL 16
* **ORM**: SQLAlchemy
* **Containerization**: Docker & Docker Compose

---

## 📋 Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd inventory-concurrency
    ```

2.  **Start the Services**:
    ```bash
    docker-compose up --build
    ```

3.  **Access the API**:
    * **Swagger Documentation**: `http://localhost:8080/docs`
    * **Health Check**: `http://localhost:8080/health`

---

## 🧪 Testing Guide (Swagger UI)

Navigate to `http://localhost:8080/docs` to test the endpoints manually.

### 1. Initialize Environment
* **Endpoint**: `POST /api/products/reset`
* **Action**: Resets stock for Product 1 to 100 and Product 2 to 50.
* **Expected Output**: `200 OK` — `{"message": "Product inventory reset successfully."}`

### 2. Verify Product State
* **Endpoint**: `GET /api/products/{id}`
* **Parameter**: `id: 1`
* **Expected Output**: `200 OK` — `{"id": 1, "name": "Super Widget", "stock": 100, "version": 1}`.

### 3. Test Pessimistic Locking
* **Method**: `POST`
* **Endpoint**: `/api/orders/pessimistic`
* **Body**:
    ```json
    {
      "productId": 1,
      "quantity": 10,
      "userId": "user_pessimistic"
    }
    ```
* **Expected Output**: `201 Created` — Order details with `status: "SUCCESS"` and `stockRemaining: 90`.

### 4. Test Optimistic Locking
* **Method**: `POST`
* **Endpoint**: `/api/orders/optimistic`
* **Body**:
    ```json
    {
      "productId": 2,
      "quantity": 5,
      "userId": "user_optimistic"
    }
    ```
* **Expected Output**: `201 Created` — Order details with an incremented `newVersion`.

### 5. Verify Conflicts (Requirement 9)
* **Action**: Use two simultaneous requests to the optimistic endpoint for the same product.
* **Expected Output**: The system detects the version mismatch. After 3 failed retries, the server returns a `409 Conflict`.

---

## 🧠 Implementation Decisions

### **1. Pessimistic Locking (Requirement 1.5)**
* **Strategy**: Uses SQLAlchemy's `.with_for_update()` which translates to a `SELECT ... FOR UPDATE` SQL command.
* **Why**: This is ideal for high-contention scenarios where we want to prevent conflicts entirely by making requests wait in a queue.
* **Trade-off**: Higher data integrity but can lead to slower performance if many users are waiting for the same row.

### **2. Optimistic Locking (Requirement 1.7 & 1.9)**
* **Strategy**: Uses a `version` column. The update only succeeds if the version in the database matches the version the application initially read.
* **Retry Logic**: Implements a **3-retry mechanism** with **exponential backoff** (doubling the wait time between retries).
* **Why**: This is more "optimistic" and faster for low-contention environments as it doesn't hold database locks while the application processes logic.  

## 📊 Concurrency Strategy Comparison

The system implements two distinct locking strategies to handle race conditions during high-volume ordering.

| Feature | Pessimistic Locking | Optimistic Locking |
| :--- | :--- | :--- |
| **Database Mechanism** | Uses `SELECT ... FOR UPDATE` to lock the row. | Uses a `version` column for comparison. |
| **Transaction Flow** | Other requests wait in a queue for the lock. | Requests fail fast if versions don't match. |
| **Conflict Handling** | Conflicts are prevented by blocking concurrent access. | Conflicts are resolved via a **3-retry loop**. |
| **Lock Monitoring** | Visible in `pg_locks` as `RowShareLock`. | Not visible as a database lock. |
| **Performance** | Better for extreme high-contention on one item. | Better for high-scale distributed systems. |



### **Strategic Decision Points**
* **Pessimistic**: Chosen for operations where inventory integrity is paramount and waiting is acceptable to avoid any user-facing errors.
* **Optimistic**: Chosen to maximize system throughput by avoiding long-held locks, using **exponential backoff** to spread out retry attempts and reduce collision density.
## 📊 Verification Scripts

For high-concurrency testing and lock monitoring, use the provided scripts in a **Git Bash** terminal:

* **Concurrency Test**: `./concurrent-test.sh [pessimistic|optimistic]`.
* **Lock Monitor**: `./monitor-locks.sh` (Displays `RowShareLock` on the `products` table).