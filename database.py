import sqlite3


# Create Database & Tables
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Chats Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        role TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES chats(id)
    )
    """)

    conn.commit()
    conn.close()


# Create New Chat
def create_chat(title="New Chat"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chats (title) VALUES (?)",
        (title,)
    )

    conn.commit()

    chat_id = cursor.lastrowid

    conn.close()

    return chat_id


# Save Message
def save_message(chat_id, role, message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO messages(chat_id, role, message)
    VALUES (?, ?, ?)
    """, (chat_id, role, message))

    conn.commit()
    conn.close()


# Get All Chats
def get_chats():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM chats
    ORDER BY created_at DESC
    """)

    chats = cursor.fetchall()

    conn.close()

    return chats


# Get Messages of One Chat
def get_messages(chat_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, message
    FROM messages
    WHERE chat_id = ?
    ORDER BY created_at ASC
    """, (chat_id,))

    messages = cursor.fetchall()

    conn.close()

    return messages


# Delete Chat
def delete_chat(chat_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM messages WHERE chat_id=?",
        (chat_id,)
    )

    cursor.execute(
        "DELETE FROM chats WHERE id=?",
        (chat_id,)
    )

    conn.commit()
    conn.close()


# Test
if __name__ == "__main__":

    init_db()

    chat_id = create_chat()

    print("New Chat Created!")
    print("Chat ID:", chat_id)

    save_message(chat_id, "user", "Hello AI")
    save_message(chat_id, "assistant", "Hello! How can I help you?")

    print("\nAll Chats:")
    print(get_chats())

    print("\nMessages:")
    print(get_messages(chat_id))