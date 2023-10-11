from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
import os

# Initialize a Spark session
spark = SparkSession.builder \
    .appName("CSVProcessingJob") \
    .getOrCreate()

# S3 URIs
source_bucket = "s3://application-migration-s3-raw/wordpress-db/"
destination_bucket = "s3://application-migration-s3-processed/wordpress-db/"

# List of folders to process
folders_to_process = [
    "wp_comments", "wp_options", "wp_postmeta", "wp_posts", "wp_term_relationships",
    "wp_term_taxonomy", "wp_termmeta", "wp_terms", "wp_usermeta", "wp_users",
    "wp_woocommerce_order_itemmeta", "wp_woocommerce_order_items", "wp_woocommerce_shipping_zone_locations",
    "wp_woocommerce_shipping_zone_methods", "wp_woocommerce_shipping_zones"
    # Add the names of the other 15/28 folders here
]

# Iterate through folders
for folder in folders_to_process:
    
    source_uri = source_bucket + folder + "/LOAD00000001.csv"
    destination_uri = destination_bucket + folder + "/"

    # Read the CSV file into a DataFrame
    df = spark.read.csv(source_uri, header=False, inferSchema=True)

    # Add a new column with 'O' for non-empty rows
    df_with_o = df.withColumn("NewColumn", lit("O"))

    # Reorder the columns with NewColumn as the first column
    columns = ["NewColumn"] + [col_name for col_name in df_with_o.columns if col_name != "NewColumn"]
    df_with_o = df_with_o.select(*columns)

    # Write the DataFrame back to S3 as a CSV without a header
    df_with_o.write.csv(destination_uri, header=False, mode="overwrite")

# Stop the Spark session
spark.stop()
