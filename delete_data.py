import pymysql

# SingleStore connection details
HOST = '127.0.0.1'
PORT = 3306
USER = 'root'
PASSWORD = 'password'
DATABASE = 'maritimedata'

def clear_table_data(table_name):
    connection = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name}")
            connection.commit()
            print(f"Data from {table_name} cleared successfully.")
    except Exception as e:
        print(f"Error clearing data from {table_name}: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    tables_to_clear = ['maritime_data', 'ship_routes']
    for table in tables_to_clear:
        clear_table_data(table)