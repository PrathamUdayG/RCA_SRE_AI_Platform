# database.py

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_db_connection():
    """
    Creates and returns a PostgreSQL connection.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def create_logs_table():
    """
    Creates the ssh_command_logs table if it doesn't exist.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_command_logs (
            id SERIAL PRIMARY KEY,
            host VARCHAR(255) NOT NULL,
            command VARCHAR(255) NOT NULL,
            output TEXT,
            error TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()

    cursor.close()
    conn.close()


def save_log(host, command, output, error):
    """
    Saves a command execution log into PostgreSQL.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ssh_command_logs
        (host, command, output, error)
        VALUES (%s, %s, %s, %s)
    """, (host, command, output, error))

    conn.commit()

    cursor.close()
    conn.close()