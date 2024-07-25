from datetime import datetime, date

COUNT_USER_QUERY = """
SELECT COUNT(*) FROM user;
"""

INSERT_USER_QUERY = """
INSERT
    INTO user(created_by, modified_by, created_at, modified_at, version, date_, username)
    VALUES (:created_by, :modified_by, :created_at, :modified_at, :version, :date_, :username)
"""

COUNT_USER_BALANCE_QUERY = """
SELECT COUNT(*) FROM user_balance;
"""

INSERT_USER_BALANCE_QUERY = """
INSERT
    INTO user_balance(created_by, modified_by, created_at, modified_at, version, user_id,
                      initial_amount, final_amount, creation_date)
    VALUES (:created_by, :modified_by, :created_at, :modified_at, :version, :user_id,
                      :initial_amount, :final_amount, :creation_date)
"""

INITIAL_USERS = [
    dict(
        id=1,
        username="default-user",
        date_=date.today(),
        created_by="root",
        modified_by="root",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1,
    ),
    dict(
        id=2,
        username="dummy-user-1",
        date_=date.today(),
        created_by="root",
        modified_by="root",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1,
    ),
    dict(
        id=3,
        username="dummy-user-2",
        date_=date.today(),
        created_by="root",
        modified_by="root",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1,
    ),
    dict(
        id=4,
        username="dummy-user-3",
        date_=date.today(),
        created_by="root",
        modified_by="root",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1,
    ),
    dict(
        id=5,
        username="dummy-user-4",
        date_=date.today(),
        created_by="root",
        modified_by="root",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1,
    ),
    dict(
        id=6,
        username="dummy-user-5",
        date_=date.today(),
        created_by="root",
        modified_by="root",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        version=1,
    ),
]

INITIAL_BALANCES = [
    dict(
        id=1,
        creation_date=datetime.now(),
        user_id=1,
        transaction_id=0,
        initial_amount=0,
        final_amount=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        created_by="root",
        modified_by="root",
        version=1,
    ),
    dict(
        id=2,
        creation_date=datetime.now(),
        user_id=2,
        initial_amount=0,
        final_amount=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        created_by="root",
        modified_by="root",
        version=1,
    ),
    dict(
        id=3,
        creation_date=datetime.now(),
        user_id=3,
        initial_amount=0,
        final_amount=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        created_by="root",
        modified_by="root",
        version=1,
    ),
    dict(
        id=4,
        creation_date=datetime.now(),
        user_id=4,
        initial_amount=0,
        final_amount=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        created_by="root",
        modified_by="root",
        version=1,
    ),
    dict(
        id=5,
        creation_date=datetime.now(),
        user_id=5,
        initial_amount=0,
        final_amount=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        created_by="root",
        modified_by="root",
        version=1,
    ),
    dict(
        id=6,
        creation_date=datetime.now(),
        user_id=6,
        initial_amount=0,
        final_amount=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        created_by="root",
        modified_by="root",
        version=1,
    ),
]
