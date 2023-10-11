import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import boto3

# Initialize a Spark context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Get job parameters
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# S3 URIs
source_bucket = "application-migration-s3-raw"
destination_bucket = "application-migration-s3-processed"

# Initialize an S3 client
s3 = boto3.client('s3')

# List objects in the source bucket
response = s3.list_objects_v2(Bucket=source_bucket)

# Start the AWS Glue job
job.init(args['JOB_NAME'], args)

# Iterate through objects and copy them to the destination bucket
for obj in response.get('Contents', []):
    object_key = obj['Key']

    # Check if the object_key does not contain "LOAD00000001"
    if "LOAD00000001" not in object_key:
        # Copy the object to the destination bucket
        s3.copy_object(CopySource={'Bucket': source_bucket, 'Key': object_key},
                       Bucket=destination_bucket, Key=object_key)

# Stop the AWS Glue job
job.commit()