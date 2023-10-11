import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node AWS Glue Data Catalog - 2
AWSGlueDataCatalog2_node1693984742642 = glueContext.create_dynamic_frame.from_catalog(
    database="wordpress-db",
    table_name="clickstream_data",
    transformation_ctx="AWSGlueDataCatalog2_node1693984742642",
)

# Script generated for node AWS Glue Data Catalog - 1
AWSGlueDataCatalog1_node1693984741935 = glueContext.create_dynamic_frame.from_catalog(
    database="wordpress-db",
    table_name="wp_woocommerce_order_items",
    transformation_ctx="AWSGlueDataCatalog1_node1693984741935",
)

# Script generated for node Change Schema - 2
ChangeSchema2_node1693903894215 = ApplyMapping.apply(
    frame=AWSGlueDataCatalog2_node1693984742642,
    mappings=[
        ("productid", "int", "productid", "int"),
        ("productname", "string", "productname", "string"),
        ("department", "string", "department", "string"),
        ("price", "double", "price", "double"),
        ("productdetails.color", "string", "productdetails.color", "string"),
        ("productdetails.material", "string", "productdetails.material", "string"),
        ("productdetails.comments", "string", "productdetails.comments", "string"),
        ("partition_0", "string", "partition_0", "string"),
        ("partition_1", "string", "partition_1", "string"),
        ("partition_2", "string", "partition_2", "string"),
        ("partition_3", "string", "partition_3", "string"),
    ],
    transformation_ctx="ChangeSchema2_node1693903894215",
)

# Script generated for node Change Schema - 1
ChangeSchema1_node2 = ApplyMapping.apply(
    frame=AWSGlueDataCatalog1_node1693984741935,
    mappings=[
        ("col0", "string", "col0", "string"),
        ("col1", "long", "col1", "int"),
        ("col2", "string", "col2", "string"),
        ("col3", "string", "col3", "string"),
        ("col4", "long", "col4", "long"),
    ],
    transformation_ctx="ChangeSchema1_node2",
)

# Script generated for node Join
Join_node1693903927084 = Join.apply(
    frame1=ChangeSchema1_node2,
    frame2=ChangeSchema2_node1693903894215,
    keys1=["col1"],
    keys2=["productid"],
    transformation_ctx="Join_node1693903927084",
)

# Script generated for node Change Schema - 3
ChangeSchema3_node1693903973765 = ApplyMapping.apply(
    frame=Join_node1693903927084,
    mappings=[
        ("col1", "int", "col1", "int"),
        ("col2", "string", "col2", "string"),
        ("col3", "string", "col3", "string"),
        ("col4", "long", "col4", "long"),
        ("productid", "int", "productid", "int"),
        ("productname", "string", "productname", "string"),
        ("department", "string", "department", "string"),
        ("price", "double", "price", "double"),
        ("productdetails.color", "string", "productdetails.color", "string"),
        ("productdetails.material", "string", "productdetails.material", "string"),
        ("productdetails.comments", "string", "productdetails.comments", "string"),
    ],
    transformation_ctx="ChangeSchema3_node1693903973765",
)

# Script generated for node Amazon S3
AmazonS3_node1693984852811 = glueContext.write_dynamic_frame.from_options(
    frame=ChangeSchema3_node1693903973765,
    connection_type="s3",
    format="glueparquet",
    connection_options={
        "path": "s3://application-migration-s3-processed/joint-tables/",
        "partitionKeys": [],
    },
    format_options={"compression": "snappy"},
    transformation_ctx="AmazonS3_node1693984852811",
)

job.commit()
