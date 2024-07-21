https://www.kaggle.com/datasets/bwandowando/2013-noaa-ais-dataset?select=2023_NOAA_AIS_logs_01.parquet

docker-compose up

docker exec -it kafka kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic maritimedata

docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic maratimedata --from-beginning

CREATE DATABASE maritimedata;
USE maritimedata;

CREATE TABLE IF NOT EXISTS maritime_data (
    MMSI BIGINT,
    BaseDateTime DATETIME,
    LAT DOUBLE,
    LON DOUBLE,
    SOG DOUBLE,
    COG DOUBLE,
    Heading DOUBLE,
    GeoPoint GEOGRAPHYPOINT
);

DESCRIBE maritime_data;

docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kafka

CREATE PIPELINE maritime_pipeline
AS LOAD DATA KAFKA 'kafka:29092/maritimedata'
INTO TABLE maritime_data
format JSON;

start pipeline maritime_pipeline;

SHOW PIPELINEs;

select * from maritime_data;

CREATE ROWSTORE TABLE IF NOT EXISTS ship_routes (
    MMSI BIGINT,
    month DATE,
    GeoLine GEOGRAPHY,
    PRIMARY KEY (MMSI, month)
);

CREATE TABLE IF NOT EXISTS trigger_tracker (
    trigger_name VARCHAR(255),
    last_triggered DATETIME,
    PRIMARY KEY (trigger_name)
    );


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

insert into trigger_tracker values('StorePolyLine', '2023-01-01 00:00:00');

CALL StorePolyLine();
