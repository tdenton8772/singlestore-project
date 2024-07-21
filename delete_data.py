import pymysql
from subprocess import call

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

def recreate_pipeline():
    connection = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP PIPELINE maritime_pipeline")
            connection.commit()
            print(f"Dropped Pipeline")

            cursor.execute(f"CREATE PIPELINE maritime_pipeline AS LOAD DATA KAFKA 'kafka:29092/maritimedata' SKIP DUPLICATE KEY ERRORS INTO TABLE maritime_data format JSON;")
            connection.commit()
            print(f"Created Pipeline")

            cursor.execute(f"START PIPELINE maritime_pipeline")
            connection.commit()
            print(f"Started Pipeline")

    except Exception as e:
        print(f"Error clearing data from {table_name}: {e}")
    finally:
        connection.close()


def clear_kafka_data():
    call(["docker", "exec", "-it", "kafka", "kafka-topics", "--delete", "--bootstrap-server", "localhost:9092", "--topic", "maritimedata"])
    call(["docker", "exec", "-it", "kafka", "kafka-topics", "--create", "--bootstrap-server", "localhost:9092", "--replication-factor", "1", "--partitions", "1", "--topic", "maritimedata"])

if __name__ == "__main__":
    tables_to_clear = ['maritime_data', 'ship_routes']
    for table in tables_to_clear:
        clear_table_data(table)
    clear_kafka_data()
    recreate_pipeline()