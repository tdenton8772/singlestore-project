import fastparquet
import json
import datetime
from kafka import KafkaProducer, KafkaAdminClient
from subprocess import call

call(['python', 'delete_data.py'])

def list_kafka_topics(bootstrap_servers):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    topics = admin_client.list_topics()
    admin_client.close()
    return topics

# Define the path to your Parquet file
file_path = './2023_NOAA_AIS_logs_01.parquet'

# Kafka configuration
kafka_broker = '172.19.0.4:9092'  # Replace with your Kafka broker address
kafka_topic = 'maritimedata'  # Replace with your Kafka topic

# Open the Parquet file
fp = fastparquet.ParquetFile(file_path)

# Create a Kafka producer
producer = KafkaProducer(
    bootstrap_servers=[kafka_broker],
    value_serializer=lambda m: json.dumps(m).encode('ascii')
)

# Check Kafka connection
try:
    producer.partitions_for(kafka_topic)
    print(f"Successfully connected to Kafka broker at {kafka_broker}")
    available_topics = list_kafka_topics([kafka_broker])
    print(f"Available topics: {available_topics}")
except Exception as e:
    print(f"Failed to connect to Kafka broker at {kafka_broker}: {e}")
    exit(1)

# Function to convert row to dictionary and handle non-serializable objects
def row_to_serializable_dict(row, columns):
    result = {}
    for column in columns:
        value = row[column]
        if isinstance(value, (datetime.datetime, datetime.date)):
            result[column] = value.isoformat()
        else:
            result[column] = value
    return result

# Function to add GeoPoint using WKT format
def add_geopoint(row_dict):
    if 'LAT' in row_dict and 'LON' in row_dict:
        lat = row_dict['LAT']
        lon = row_dict['LON']
        row_dict['GeoPoint'] = f"POINT({lon} {lat})"
    return row_dict

# Iterate through row groups
for row_group in fp.iter_row_groups():
    columns = row_group.columns
    data_dict = row_group.to_dict()
    for i in range(len(data_dict[columns[0]])):
        row = {column: data_dict[column][i] for column in columns}
        row_dict = row_to_serializable_dict(row, columns)
        row_dict = add_geopoint(row_dict)
        producer.send(kafka_topic, row_dict)
    producer.flush()

# Close the Kafka producer
producer.close()