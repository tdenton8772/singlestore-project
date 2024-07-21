https://www.kaggle.com/datasets/bwandowando/2013-noaa-ais-dataset?select=2023_NOAA_AIS_logs_01.parquet

`docker-compose up`

`docker exec -it kafka kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic maritimedata`

`docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic maratimedata --from-beginning`

`CREATE DATABASE maritimedata;`

`USE maritimedata;`

```sql
CREATE TABLE IF NOT EXISTS maritime_data (
    MMSI BIGINT,
    BaseDateTime DATETIME,
    LAT DOUBLE,
    LON DOUBLE,
    SOG DOUBLE,
    COG DOUBLE,
    Heading DOUBLE,
    GeoPoint GEOGRAPHYPOINT,
    PRIMARY KEY(MMSI, BaseDateTime),
    SHARD KEY(MMSI),
    SORT KEY(MMSI, BaseDateTime)
);
```

`DESCRIBE maritime_data;`

`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kafka`


```sql
CREATE PIPELINE maritime_pipeline
AS LOAD DATA KAFKA 'kafka:29092/maritimedata' SKIP DUPLICATE KEY ERRORS
INTO TABLE maritime_data 
format JSON;
```

`start pipeline maritime_pipeline;`

`SHOW PIPELINEs;`

`select * from maritime_data;`

```sql
CREATE ROWSTORE TABLE IF NOT EXISTS ship_routes (
    MMSI BIGINT,
    month DATE,
    GeoLine LONGTEXT,
    PRIMARY KEY (MMSI, month),
    SHARD KEY(MMSI)
);
```

```sql
CREATE TABLE IF NOT EXISTS trigger_tracker (
    trigger_name VARCHAR(255),
    last_triggered DATETIME,
    PRIMARY KEY (trigger_name)
    );
```


```sql
DELIMITER //
CREATE OR REPLACE PROCEDURE StorePolyLine() as 
begin
    Insert into ship_routes SELECT MMSI,
                                    DATE(CONCAT(DATE_FORMAT(BaseDateTime, '%Y-%m'), '-01')) AS month,
                                    CONCAT('LINESTRING(', GROUP_CONCAT(CONCAT_WS(' ', LON, LAT) ORDER BY BaseDateTime SEPARATOR ', '), ')') AS GeoLine
                                FROM maritime_data
                                WHERE BaseDateTime >= (select last_triggered from trigger_tracker where trigger_name = "StorePolyLine")
                                GROUP BY MMSI, DATE_FORMAT(BaseDateTime, '%Y-%m');
end //
DELIMITER ;
```

`insert into trigger_tracker values('StorePolyLine', '2023-01-01 00:00:00');`

`CALL StorePolyLine();`

`python load_data.py`

`python app.py`

`python delete_data.py`

Go to localhost:5000 to see dashboard. 
