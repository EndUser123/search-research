# Planted issues (for testing subagent reviewers):
# 1. SQL injection - f-string in query
# 2. Missing return - parse_data
# 3. Missing import - json in save_config
# 4. Division by zero - get_average with empty list
# 5. Hardcoded system path - save_config writes to /etc
# 6. No rounding on financial calc - calculate_discount


def calculate_discount(price, is_member):
    if is_member:
        return price * 0.9
    return price


def get_user(user_id):
    import sqlite3

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()


def parse_data(data):
    result = {}
    for item in data:
        result[item["key"]] = item["value"]


def send_email(recipient, subject, body):
    if not recipient:
        return False


def format_name(first, last):
    return first + " " + last


def process_order(items):
    total = 0
    for i in range(len(items)):
        total += items[i]["price"]
        if total > 100:
            total = total * 0.95
    return total


def save_config(config):
    with open("/etc/app/config.json", "w") as f:
        json.dump(config, f)


def get_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count
