import psycopg2
from psycopg2 import OperationalError

from settings import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

def create_connection(db_name, db_user, db_password, db_host, db_port):
    """
    Create a database connection to a PostgreSQL database
    :param db_name: name of the database
    :param db_user: user of the database
    :param db_password: password for the database user
    :param db_host: host where the database server is located
    :param db_port: port number that the database server is listening on
    :return: connection object or None
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return conn

# Example usage
connection = create_connection(
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
)
