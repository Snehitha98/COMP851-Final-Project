import psycopg2
import boto3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT



try:
   # boto3
   sqs = boto3.resource('sqs',aws_access_key_id =  'xxxxxxxxxxxxxxxxx',
                        aws_secret_access_key = 'xxxxxxxxxxxxxxxxxxxxxxx')
   queue = sqs.create_queue(QueueName='sm1552_pwtc', Attributes={'DelaySeconds': '3'})

   # connecting to postgis
   connection = psycopg2.connect(user="postgres",
                                  password="CT13root",
                                  host="localhost")
   connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT);
   cursor = connection.cursor()

   # create database
   cursor.execute("drop database if exists pwtc;")

   create_database = """create database pwtc;"""
   cursor.execute(create_database)
   connection.commit()

   # create extension postgis if not exists
   create_extension_query = """create extension if not exists postgis;"""
   cursor.execute(create_extension_query)
   connection.commit()

   # Create the table landmarks in the database
   create_tables_landmarks = """  CREATE TABLE landmarks
(
  gid character varying(5) NOT NULL,
  name character varying(50),
  address character varying(50),
  date_built character varying(10),
  architect character varying(50),
  landmark character varying(10),
  latitude double precision,
  longitude double precision,
  the_geom geometry,
  CONSTRAINT landmarks_pkey PRIMARY KEY (gid),
  CONSTRAINT enforce_dims_the_geom CHECK (st_ndims(the_geom) = 2),
  CONSTRAINT enforce_geotype_geom CHECK (geometrytype(the_geom) = 'POINT'::text OR the_geom IS NULL),
  CONSTRAINT enforce_srid_the_geom CHECK (st_srid(the_geom) = 4326)
);
"""
   cursor.execute(create_tables_landmarks)
   connection.commit()

   # create index
   create_index_landmarks = """ CREATE INDEX if not exists landmarks_the_geom_gist ON landmarks USING gist (the_geom )"""
   cursor.execute(create_index_landmarks)
   connection.commit()

   # Copy the CSV data into the database
   insert_data = """ copy landmarks(name,gid,address,date_built,architect,landmark,latitude,longitude) FROM '/home/administrator/Desktop/Individual_Landmarks.csv' DELIMITERS ',' CSV HEADER """
   cursor.execute(insert_data)
   connection.commit()

   # sending insertion info to queue
   response = queue.send_message(MessageBody='Landmarks',MessageAttributes={
      'Insertion':{
         'StringValue':'Data Uploaded Successfully!!!',
         'DataType':'String'
         }})


   queue = sqs.get_queue_by_name(QueueName='sm1552_pwtc')

   # Translate latitude and longitude into POINT geometry
   update_table = """UPDATE landmarks SET the_geom = ST_GeomFromText('POINT(' || longitude || ' ' || latitude || ')',4326) """
   cursor.execute(update_table)
   connection.commit()

   # This query returns the 5 closest landmarks to a given latitude and longitude
   select_statement = """SELECT distinct
ST_Distance(ST_GeomFromText('POINT(-87.6348345 41.8786207)', 4326), landmarks.the_geom) AS planar_degrees,
name,
architect, latitude, longitude
FROM landmarks
ORDER BY planar_degrees ASC
LIMIT 5 """
   count = 1
   cursor.execute(select_statement)
   connection.commit()
   location_details=[]
   records = cursor.fetchall()
   print("\n")
   print(f'5 closest landmarks to the latitude -87.6348345 and longitude 41.8786207')

   for row in records:
       print("\n")
       print("Location " + str(count))
       print("----------")
       print("Planar Degrees : " + str(row[0]))
       print("Name : " + str(row[1]))
       print("Architect : " + str(row[2]))
       print("Latitude : "+ str(row[3]))
       print("Longitude : "+ str(row[4]))

       count +=1
       location_details.append(str(row[0]))
       location_details.append(str(row[1]))
       location_details.append(str(row[2]))
       location_details.append(str(row[3]))
       location_details.append(str(row[4]))

   # sending location data to the queue
   response = queue.send_message(MessageBody='Landmarks',MessageAttributes={
      'Locations':{
         'StringValue':",".join(location_details),
         'DataType':'String'
         }})
   connection.commit()


except (Exception, psycopg2.Error) as error :
    if(connection):
        print(error)

finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("\n")
        print("PostgreSQL connection is closed")
