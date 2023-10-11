# Revolutionizing Analytics Data Transformation on AWS: An Implementation Guide

## Reference Architecture

![img1](/images/img1.png)

Imagine a retail giant facing intense competition and needing a data-driven strategy to stay ahead. This architecture diagram would serve as a valuable tool for them to transition to cloud-based operations and seek to enhance their analytics capabilities. Currently, the company manages a substantial volume of data on their MySQL server, and their analytics processes are predominantly manual, involving a range of disparate tools. Moreover, the organization regularly receives clickstream data from their web application detailing customer purchases, prompting a need for streamlining their data consolidation and processing efforts. The proposed solution aims to establish a robust data warehousing infrastructure to accommodate future scaling and the acquisition of additional databases. Ultimately, this infrastructure will ensure the company's capability to support increased data volumes effectively. Lastly, post-data processing, the ability to visualize the data is crucial, empowering the company to make informed business decisions grounded in data-driven insights.

## 1. Getting Started
For the purpose of this entire tutorial, unless otherwise specified, this tutorial will be entirely set up in the US West (Oregon) us-west-2. In addition, any unspecified parameters should assume their default values.

In this section, the main task is to deploy a CloudFormation template in your AWS environment, which comes pre-configured with the necessary settings.

1. Click [here](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=ApplicationMigrationWorkshop&templateURL=https://ee-assets-prod-us-east-1.s3.us-east-1.amazonaws.com/modules/migration/v1/migration_workshop_source_template.yml) to launch the CloudFormation stack in your AWS environment. 
2. Ensure that under the Specify template, the Amazon S3 URL is https://ee-assets-prod-us-east-1.s3.us-east-1.amazonaws.com/modules/migration/v1/migration_workshop_source_template.yml.
3. Click **Next** until the CloudFormation template is launched. 
4. This process should take under 5 minutes and the Status should change to `CREATE_COMPLETE`. 

	![img2](/images/img2.png)


## 2. Network Setup - Configuring the Security Group
In this section, the instructions focus on configuring the security groups necessary for the setup, ensuring secure communication within the AWS environment. 2 security groups will be created: 
1. The security group for the DMS Replication Instance and 
2. The security group for the Target Database. 

### 2.1 Configuring the security group for the DMS Replication Instance
1. Go to [VPC on the console](https://console.aws.amazon.com/vpc).
2. On the left panel, under Security, click on `Security groups`. 
3. Click on **Create security group**. Fill in the following parameter values before clicking on **Create security group**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Security group name | Replication-Instance-SG |
	| Description | Security group for replication instance |
	| VPC | TargetVPC |

### 2.2 Configuring the security group for the DMS Replication Instance
1. Go to [VPC on the console](https://console.aws.amazon.com/vpc).
2. On the left panel, under Security, click on `Security groups`. 
3. Click on **Create security group**. Fill in the following parameter values.

	| Parameter | Values |
	| ------------- |-------------|
	| Security group name | Database-SG |
	| Description | Security group for target database |
	| VPC | TargetVPC |
4. In the Inbound rules section, click on **Add rule** and configure the rule to allow inbound traffic from the DMS Replication Instance security group (`Replication-Instance-SG`) on port 3306. 

	| Parameter | Values |
	| ------------- |-------------|
	| Type | MYSQL/Aurora |
	| Port range | 3306 |
	| Source | Custom ; Replication-Instance-SG |
5. Click on **Create security group**. 


## 3. Setting up the MySQL server that is on-premises
This section focuses on setting up the MySQL server that resides on-premises, and it outlines these instructions to facilitate a  database migration process. The objective is to minimize downtime during the migration by implementing Change Data Capture (CDC) for continuous replication from the source database (on-premises) to the target database in the cloud.

### 3.1 Setting up the source database by SSH Client
1. Go to [CloudFormation on the console](https://us-west-2.console.aws.amazon.com/cloudformation). 
2. Click on the stack name: `ApplicationMigrationWorkshop`
3. Under the `Outputs` tab, click on the SSHKeyURL link to download the key pair file. This key pair file is required for secure SSH access to the source database server. 

	![img3](/images/img3.png)

4. Go to [EC2 on the console](https://us-west-2.console.aws.amazon.com/ec2/). Click on `Instances`, followed by the Instance ID of the `Source-DBServer`. 
5. Click on the **Connect** button and select the `SSH Client` tab. Follow the instructions accordingly to establish an SSH connection using an SSH client. 
6. Tip: Open the terminal locally and `cd` to the folder that contains the key file `.pem` that you had downloaded. E.g. if the file is located in the downloads folder then run the following command: `cd downloads`.


### 3.2 Setting up the virtual MySQL Workbench
This section involves setting up the virtual MySQL Workbench on your local terminal. These steps are essential for ensuring data consistency and replication during the migration process.
1. Create a user to login to MySQL with the following code: 
	```
	sudo mysql
	ALTER USER ‘root’@‘localhost’ IDENTIFIED WITH mysql_native_password BY ‘<password>’;
	FLUSH PRIVILEGES; 
	```
	Remember to change the `<password>` placeholder with your own. 


2. Exit and login again with your newly created credentials. 
	```
	Exit;
	sudo mysql -u root -p<password> 
	```
3. Grant privileges to the root database user. Run the following commands: 
	```
	GRANT REPLICATION CLIENT ON *.* TO 'root';
	GRANT REPLICATION SLAVE ON *.* TO 'root';
	GRANT SUPER ON *.* TO 'root';
	```
4. Create a folder in the directory for the bin logs.
	```
	sudo su - 
	mkdir /var/lib/mysql/binlogs
	chown -R mysql\:mysql /var/lib/mysql/binlogs
	exit;
	```
5. Add the following configuration file to enable binary logging. 
	```
	sudo su -
	cp /etc/mysql/mysql.conf.d/mysqld.cnf /etc/mysql/my.cnf
	chown -R mysql\:mysql /etc/mysql/my.cnf
	cat <<EOF >> /etc/mysql/my.cnf
	server_id=1
	log-bin=/var/lib/mysql/binlogs/log
	binlog_format=ROW
	expire_logs_days=1
	binlog_checksum=NONE
	binlog_row_image=FULL
	log_slave_updates=TRUE
	performance_schema=ON
	EOF
	exit;
	```
6. Restart MySQL service to apply the changes. 
	```
	sudo systemctl restart mysql
	```
7. Login to the MySQL workbench again and check that the binary log have been enabled. 
	```
	sudo mysql -u root -p<password>
	
	select variable_value as "BINARY LOGGING STATUS (log-bin) :: "
	 from performance_schema.global_variables where variable_name='log_bin';
	
	select variable_value as "BINARY LOG FORMAT (binlog_format) :: "
	 from performance_schema.global_variables where variable_name='binlog_format';
	
	exit
	```
	Remember to change the `<password>` placeholder with your own. 
	<br><br>
	You should see the output similar to the screenshot below where the `BINARY LOGGIN STATUS` is `ON` and the `BINARY LOG FORMAT` is `ROW`.
	
	![img4](/images/img4.png)


## 4. Setting up the Target S3 Bucket
In this section, we will be creating an S3 bucket and its permission for the MySQL database to be stored in the AWS Cloud after the migration. If you would like to implement the Amazon Kinesis Data Stream and Amazon Kinesis Data Firehose in the ingestion pipeline, kindly refer to this [document](docs/MySQL%20data%20to%20S3%20using%20Kinesis.md). 

### 4.1 Create the Target S3 Bucket
1. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
2. Click on **Create Bucket**, fill the following parameter values before clicking on **Create bucket**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Bucket name | application-migration-s3-raw |
	| AWS Region | US West (Oregon) us-west-2 |

### 4.2 Create the Role for DMS to access the Target S3 Bucket
This section involves creating a role that allows AWS Database Migration Service (DMS) to access and interact with the target S3 bucket. 

1. Go to [Identity and Access Management (IAM) on the console](https://console.aws.amazon.com/iamv2/). 
2. On the left panel, select `Roles`, followed by **Create role**. 
3. Enter the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Trusted entity type | AWS service |
	| Use cases for other AWS services: | DMS |
4. Select the radio button for `DMS` and click **Next**. 
5. In the search field for the Permission policies, search for this policy `AmazonS3FullAccess`, select the policy and then choose **next**. 
6. Fill in the role name as `DMS_to_S3_role`, followed by **Create role**. 
7. Once created, copy the ARN of that role, `arn:aws:iam::<AWS account ID>:policy/DMS_to_S3_role`, and keep it for use in Section 5.4 Configure the Target Endpoint. 


## 5. Setting up Database Migration Service (DMS)
This section provides a comprehensive guide to setting up and configuring the components of the Database Migration Service (DMS) for the migration process. 

### 5.1 Configure the Subnet Group
This section serves as a guide to configure the Subnet Group in DMS. This is done by defining the subnets within the Virtual Private Cloud (VPC) that the DMS will operate in. This is important for network isolation and security.

1. Go to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). 
2. On the left panel, click on `Subnet groups` followed by **Create subnet group** button. 
3. Enter the following parameter values before clicking on **Create subnet group**.

	| Parameter | Values |
	| ------------- |-------------|
	| Name | DMS-subnet-group |
	| Description | DMS Subnet group VPC |
	| VPC | TargetVPC |
	| Add subnets | TargetVPC-public-a ; TargetVPC-public-b |

### 5.2 Configure the Replication Instance
The Replication Instance acts as the intermediary between the source and target databases. It specifies settings such as the replication instance name, network details, and security groups to ensure reliable data replication.


1. Go to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). 
2. On the left panel, click on `Replication Instances` followed by **Create replication instance** button. 
3. Enter the following parameter values. If the parameter is not mentioned in the table, always leave it to the default value. 

	| Parameter | Values |
	| ------------- |-------------|
	| Name | replication-instance |
	| High Availability | Dev or test workload (Single-AZ) |
	| VPC for IPv4 | TargetVPC |
	| Replication subnet group | DMS-subnet-group | 
	| Public accessible | checked |
4. Expand the `Advanced settings` and use the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Availability zone | us-west-2a |
	| VPC security groups | Replication-Instance-SG |
5. Click on **Create replication instance**. 
6. Once created, wait for the Status to be `Available`. Copy the Public IP address of the replication instance as `xx.xxx.xxx.xxx`. 

	![img5](/images/img5.png)

7. Go to [VPC on the console](https://us-west-2.console.aws.amazon.com/vpc/).
8. On the left panel, select `Security groups` and click on `DBServerSG` Security group ID. Click on **Edit inbound rules**.
9. Enter the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Type | MYSQL/Aurora |
	| Source | Custom ; xx.xxx.xxx.xxx/32|
	
	![img6](/images/img6.png)

10. Click on **Save rules**. This will allow the replication instance to access the source database. 

### 5.3 Configure the Source Endpoint
1. Go to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). 
2. Click on `Endpoints` followed by **Create endpoint**. 
3. Enter the following parameter values. If the parameter is not mentioned in the table, always leave it to the default value. 

	| Parameter | Values |
	| ------------- |-------------|
	| Endpoint type | Source endpoint |
	| Endpoint identifier | source-endpoint |
	| Source engine | MySQL |
	| Access to endpoint database | Provide access information manually |
	| Server name | ec2-\<string-of-numbers>.us-west-2.compute.amazonaws.com | 
	| Port | 3306 | 
	| User name | root |
	| Password | \<password> |

	Remember to change the `<password>` and `<string-of-numbers>` placeholder with your own. The Server name can be obtained from [CloudFormation](https://us-west-2.console.aws.amazon.com/cloudformation/) Stack under `Outputs`, DBServerDNSName.  
	
	![img7](/images/img7.png)

4. Expand the `Test endpoint connection (optional)` section. 
5. Select the following parameter values and click **Run test**. 

	| Parameter | Values |
	| ------------- |-------------|
	| VPC | TargetVPC |
	| Replication instance | replication-instance |
6. After a minute, the Status should indicate `successful`, thereafter, proceed to click on  **Create endpoint**. 

### 5.4 Configure the Target Endpoint
1. Go to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). 
2. Click on `Endpoints` followed by **Create endpoint**. 
3. Enter the following parameter values. If the parameter is not mentioned in the table, always leave it to the default value. 

	| Parameter | Values |
	| ------------- |-------------|
	| Endpoint type | Target endpoint |
	| Endpoint identifier | target-endpoint |
	| Source engine | Amazon S3 |
	| Amazon Resource Name (ARN) for service access role | arn:aws:iam::\<AWS account ID>:policy/DMS_to_S3_role |
	| Bucket name | application-migration-s3-raw |

	The Amazon Resource Name (ARN) for service access role can be obtained from Section 4.2. 

4. Expand the `Test endpoint connection (optional)` section. 
5. Select the following parameter values and click on **Run test**. 

	| Parameter | Values |
	| ------------- |-------------|
	| VPC | TargetVPC |
	| Replication instance | replication-instance |
6. After a minute, the Status should indicate `successful`, thereafter, proceed to click on **Create endpoint**. 


### 5.5 Configure the Database Replication Task
1. Go to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). 
2. On the left panel, click on `Database migration tasks` followed by **Create task**. 
3. Enter the following parameter values. If the parameter is not mentioned in the table, always leave it to the default value. 

	| Parameter | Values |
	| ------------- |-------------|
	| Task identifier | replication-task |
	| Replication instance | replication-instance | 
	| Source database endpoint | source-endpoint |
	| Target database endpoint | target-endpoint |
	| Migration type | Migrate existing data and replicate ongoing changes | 
4. Enter the following parameter values for the `Task settings` section. 

	| Parameter | Values |
	| ------------- |-------------|
	| Editing mode | Wizard |
	| Target table preparation mode | Do nothing |
	| Validation | Checked (if possible) |
	| Task logs | Checked | 
5. Enter the following parameter values for the `Task mappings` section. Click on **Add new selection rule**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Editing mode | Wizard |
	| Schema | Enter a schema |
	| Source name | wordpress-db |
6. Lastly, in the Migration task startup configuration, select `Automatically on create`. Complete by clicking on **Create task** for the migration tasks to start. 
7. An indication that the replication tasks is completed and undergoing CDC will be the task Status is `Load complete, replication ongoing` and the Progress shows `100%`.

	![img8](/images/img8.png)

8. You can view the information on the tables being replicated to the S3 bucket, click on the `replication-task` followed by the `Table statistics` tab. 

### 5.6 Validating the Change Data Capture (CDC) Functionality 
Up until now, we have completed the connection of the souce MySQL database, AWS DMS and the landing S3 bucket (Raw). This section involves inserting data into the source MySQL database and verifying its replication to the S3 bucket, ensuring data integrity throughout the migration.

![img9](/images/img9.png)

1. Open up the terminal locally and SSH into your virtual MySQL workbench. We can now check how many users there are in the table `wp_terms`. The table should only have 15 rows of entries. 
	```
	sudo mysql -u root -p<password>
	
	use `wordpress-db`;
	SELECT * FROM `wordpress-db`.wp_terms;
	```
2. We will insert 4 entries into the table.
	```
	#insert into wp_terms values ('16', 'random-1', 'random-1', '1');
	#insert into wp_terms values ('17', 'random-2', 'random-2', '0');
	#insert into wp_terms values ('18', 'random-3', 'random-3', '1');
	#insert into wp_terms values ('19', 'random-4', 'random-4', '0');
	```
3. We will now check that the table have been updated in the virtual MySQL workbench. The table should have 19 rows now. 
	```
	select * from wp_terms; 
	```
4. To verify that CDC have happened and the newly inserted data have reached the S3 bucket, we can check by going to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). Click on `Database migration tasks` > `replication-task` > `Table statistics`. For the table `wp_terms`, under the Inserts column, the value is now `4`.
5. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/), click on the bucket name `application-migration-s3-raw` > `wordpress-db/` > `wp_terms/`. You will notice that the folder have 2 CSV files. The `LOAD00000001.csv` file belongs to the initial 1 time replication of copying the data from the virtual MySQL database to S3. The CSV file with the date and time, e.g. `20230905-151244585.csv` is the CDC data. 
6. Select the date and time CSV file (e.g. `20230905-151244585.csv`) > `Actions` > `Query with S3 Select` > `Run SQL query`. In the Query results, you should be able to see the 4 entries that was inserted in Step 2 of this section. 


## 6. AWS Glue
The company recognized that raw data held limited value, leading them to employ AWS Glue for data transformation and ETL processes. This encompassed tasks such as cleaning messy data, standardizing it, and enhancing it with additional information. Leveraging the AWS Glue Data Catalog, they effectively tracked metadata and data lineage. In this section, we will explore the capabilities of AWS Glue by processing data from the S3 (Raw) bucket and outputting it to the S3 (Processed) bucket. Detailed instructions on configuring AWS Glue, creating Glue Jobs for data processing, and setting up Glue Crawlers to catalog processed data ensure that data is well-prepared and organized for subsequent analysis and usage.

![img10](/images/img10.png)

### 6.1 Configure IAM Policies and Role for Glue Job
In this section, the setting up of IAM policies and role will enable Glue Jobs to access the specified resources securely.

1. Go to [IAM on the console](https://console.aws.amazon.com/iamv2/). 
2. On the left panel, click on `Policies`, followed by **Create policy**. 
3. Select the `JSON` tab and replace the Policy editor text with the following:
	```
	{
	  "Version": "2012-10-17",
	  "Statement": [
	    {
	    "Effect": "Allow",
	    "Action": "iam:PassRole",
	    "Resource":"arn:aws:iam::<AWS account ID>:role/GlueJobRole"
	    }
	  ]
	}
	```
	Replace `<AWS account ID>` with your own account ID found on the top right hand corner. 

4. Enter the Policy name as `GlueRole` and click on **Create policy**. 
5. On the left panel, click on `Roles`, and **Create Role**.
6. Enter the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Trusted entity type | AWS service |
	| Use cases for other AWS services: | Glue |
7. Select the radio button for `Glue` and click **Next**. 
8. In the search field for the Permission policies, search for the following policies, select the policy and then choose **next**. 
	1. `AmazonS3FullAccess`
	2. `AWSGlueServiceRole`
	3. `GlueRole`
	4. `AwsGlueSessionUserRestrictedNotebookPolicy`
9. Fill in the role name as `Glue_Job_Role`, followed by **Create role**. 

### 6.2 Create the Processed S3 Bucket
1. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
2. Click on **Create Bucket** and fill in the following parameter values before clicking on **Create bucket**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Bucket name | application-migration-s3-processed |
	| AWS Region | US West (Oregon) us-west-2 |
3. This bucket will store processed data after Glue Jobs have completed their tasks.

### 6.3 Configure Extract, Transform, Load (ETL) Glue Jobs for data processing

![img11](/images/img11.png)

#### 6.3.1 Create a Glue Job to process the LOAD files
The LOAD files in the S3 raw bucket are the original data moved from the MySQL database to the S3 bucket. It is a one time off process. The subsequent date time files from the CDC migration will have an additional first column that indicates D = Delete, I = Insert, U = Update. This will result in inconsistent column sizing which could result in messy data cataloging later on when the Glue Crawler is used. Hence, to ensure a consistent column size for each table, the purpose of the python script will do the following: 

1. Reads the LOAD CSV files from the S3 bucket folder (raw).
2. Adds a column in front of the first column.
3. For rows that are not empty in the file, put ‘O’ in the first column of those rows.
4. Saves the CSV file to another S3 bucket folder (processed) without the header.
5. Repeat through 15 other folders located in the source bucket.
<br>

1. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
2. On the left panel, click on `ETL jobs`. 
3. Select `Spark script editor` and click on **Create**.
4. Copy and paste the following into the Script segment. 
	```
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
	```

5. Click on the `Job details` tab and fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Name | Job 1 - Process LOAD files |
	| Description | This job reads LOAD files from the source bucket (raw), adds 'O' to non-empty rows in the first column, saves the LOAD file in the destination bucket (processed-job). It is iterated through all the 15 folders in the source bucket (raw). |
	| IAM Role | Glue_Job_Role |
	| Worker type | G 8X |
6. Click on **Save** and then **Run**. 
7. When the Glue Job is completed, the Run status will be updated as `Succeeded`. 

#### 6.3.2 Create a Glue Job to copy the CDC files from the Raw to Processed bucket
The CDC files are in the S3 Raw bucket and will need to be copied to the Processed bucket in preparation of cataloging the data. Hence, the python script will do the following: 

1. Reads the non-LOAD CSV files from the S3 bucket folder (raw).
2. Saves the CSV file to another S3 bucket folder (processed).
3. Repeat through other 15 folders located in the source bucket.
<br>

1. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
2. On the left panel, click on `ETL jobs`. 
3. Select `Spark script editor` and click on **Create**.
4. Copy and paste the following into the Script segment. 
	```
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
	```

5. Click on the `Job details` tab and fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Name | Job 2 - Copy CDC files from Raw bucket to Processed |
	| Description | This job copy all the CDC files from the source bucket (raw) to the destination bucket (processed-job). This does not include the LOAD files. |
	| IAM Role | Glue_Job_Role |
	| Worker type | G 8X |
4. Click on **Save** and then **Run**. 
5. When the Glue Job is completed, the Run status will be updated as `Succeeded`. 

### 6.4 Glue Crawlers

![img12](/images/img12.png)

1. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
2. On the left panel, click on `Crawlers` and **Create crawler**. 
3. Fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Name | wordpress-db-crawler |
	| Is your data already mapped to Glue tables? | Not yet |
4. Click on **Add a data source** and fill in the following parameter value before clicking on **Add an S3 data source**.

	| Parameter | Values |
	| ------------- |-------------|
	| S3 path | s3://application-migration-s3-processed/wordpress-db/ |
5. Click **Next** and fill in the following parameter value. 

	| Parameter | Values |
	| ------------- |-------------|
	| Existing IAM role | Glue_Job_Role |
6. Click **Next** and click **Add database** (a new tab should open). Fill in the following parameter value before clicking on **Create database**.

	| Parameter | Values |
	| ------------- |-------------|
	| Name | wordpress-db |
7. Head back to the Glue Crawler tab and press the refresh button next to Target database. Select `wordpress-db` from the dropdown. 
8. Finally click **Next** and **Create crawler**. 
9. Click on **Run crawler** and wait for the State to update to `Completed`. 


## 7. Amazon Athena
This section will cover the use of Amazon Athena to query and analyze the processed data, ensuring that query results are stored in a convenient and accessible location for further analysis and reporting purposes.

![img13](/images/img13.png)

### 7.1 Create an Endpoint storage for the Athena Queries
1. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
2. Select the `application-migration-s3-processed` bucket. We will be creating a folder for the Glue Job to store the joint-tables data after processing. 
3. Click on **Create folder**, fill in the following parameter value before clicking on **Create folder**.

	| Parameter | Values |
	| ------------- |-------------|
	| Folder name | joint-tables |
4. In the same `application-migration-s3-processed` bucket, we will create another folder for the Amazon Athena queries to be stored. 
5. Click on **Create folder**, fill in the following parameter value before clicking on **Create folder**.

	| Parameter | Values |
	| ------------- |-------------|
	| Folder name | athena-queries |

### 7.2 Querying on Athena
1. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
2. On the left panel, click on `Tables`. There should be 15 tables in total. 
3. Click on `Table data` for any one of the table. A prompt will appear, click on **Proceed**. 
4. Click on **Edit settings**. Fill in the following parameter value before clicking on **Save**.

	| Parameter | Values |
	| ------------- |-------------|
	| Location of query result | s3://application-migration-s3-processed/athena-queries |

	All the unsaved queries ran in Athena can be viewed in the S3 bucket of URI: `s3://application-migration-s3-processed/athena-queries/Unsaved/`.

6. Head back to the `Editor` Tab where you can start querying the different tables of the database `wordpress-db`.

 
## 8. Ingesting Clickstream Data
In this section, instructions essential for effectively ingesting, simulating, and cataloging clickstream data within the AWS environment, enabling data-driven insights and analytics on user interactions and behavior will be covered.

![img14](/images/img14.png)

### 8.1 Create an Endpoint storage for the Data
1. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
2. Select the `application-migration-s3-raw` bucket.
3. Click on **Create folder**. Fill in the following parameter values before clicking on **Create folder**.

	| Parameter | Values |
	| ------------- |-------------|
	| Folder name | clickstream-data |

### 8.2 Configuring Amazon Kinesis Data Stream
This section is crucial for ingesting real-time clickstream data.

1. Go to [Kinesis on the console](https://console.aws.amazon.com/kinesis/).
2. Click on **Create data stream**. Fill in the following parameter values before clicking on **Create data stream**.

	| Parameter | Values |
	| ------------- |-------------|
	| Data stream name | kds-clickstream-data |
	| Capacity mode | On-demand |
3. Once provisioned, the Status should update to `Active`.

### 8.3 Configuring Amazon Kinesis Data Firehose
The clickstream data from the Kinesis Data Stream will be input to the Kinesis Data Firehose before the data lands in the S3 bucket. 

1. On the left panel, click on **Data Firehose**. 
2. Click on **Create delivery stream**. Fill in the following parameter values before clicking on **Create delivery stream**.

	| Parameter | Values |
	| ------------- |-------------|
	| Source | Amazon Kinesis Data Streams |
	| Destination | Amazon S3 |
	| Kinesis data stream | \<click Browse and select kds-clickstream-data> |
	| Delivery stream name | kdf-clickstream-data |
	| S3 bucket destination | s3://application-migration-s3-raw |
	| S3 bucket prefix | clickstream-data/ |
	| Buffer size | 1 MiB |
	| Buffer interval | 60 seconds | 
3. Once provisioned, the Status should update to `Active`.


### 8.4 Configuring the Kinesis Data Generator
In this section, you will be deploying a CloudFormation template in your AWS cloud environment where the necessary configurations have been done. This will enable the Kinesis Data Generator to send random data to the Kinesis pipeline, simulating realistic clickstream data ingestion.  

1. Click [here](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=Kinesis-Data-Generator-Cognito-User&templateURL=https://aws-kdg-tools-us-east-1.s3.amazonaws.com/cognito-setup.json) to launch the CloudFormation stack in your AWS environment. 
2. Ensure that under the Specify template, the Amazon S3 URL is https://aws-kdg-tools-us-east-1.s3.amazonaws.com/cognito-setup.json.
3. Click **Next** and fill in the following parameter values before clicking **Next**.

	| Parameter | Values |
	| ------------- |-------------|
	| Username | root |
	| Password | \<password> |

	Remember to change the `<password>` placeholder with your own. 

4. Click **Next** until the CloudFormation template is launched. This process should take under 2 minutes and the Status should change to `CREATE_COMPLETE`.  
5. Click on the Stack Name: `Kinesis-Data-Generator-Cognito-User`. If you do not see this Stack name, remember to change the region to US East (N. Virginia) us-east-1. 
6. Click on the `Outputs` tab and click on the URL. 
7. Login using the credentials that you had created in Step 3 of this section. 
8. Fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Region | us-west-2 |
	| Stream/delivery stream | kds-clickstream-data |
	| Records per second | 2000 |
9. Copy and paste the following code into Record template: Template 1.
	```
	{"productid": {{random.number(
	        {
	            "min":1,
	            "max":5
	        }
	    )}},
	"productname": "{{commerce.productName}}",
	"department": "{{commerce.department}}",
	"price": {{commerce.price}},
	"productDetails":{"color": "{{commerce.color}}",
	"material": "{{commerce.productMaterial}}",
	"comments": "{{commerce.productAdjective}}"}
	}
	```
10. Click on **Send data**. Allow 100,000 records to be sent to Kinesis before clicking on **Stop Sending Data to Kinesis**. 
11. You can check that the data have indeed reached the assigned S3 bucket. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
12. Select the `application-migration-s3-raw` bucket > `clickstream-data/`.
13. Follow the directory to eventually reach the folder with the data files.

	![img15](/images/img15.png)


### 8.5 Configure AWS Glue Crawler
This section updates the existing Glue Crawler to include the newly ingested clickstream data. This ensures that the data is also included in the Glue Data Catalog for further processing and analysis. 

1. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
2. On the left panel, click on `Crawlers`. 
3. Select the existing `wordpress-db-crawler`, click on **Action** followed by **Edit crawler**.
4. Click the **Edit** button next to Step 2: Choose data sources and classifiers.
5. Click **Add a data source** and fill in the following parameter values before clicking on **Add an S3 data source**.

	| Parameter | Values |
	| ------------- |-------------|
	| S3 path | s3://application-migration-s3-raw/clickstream-data/ |
6. Click **Next** three times followed by **Update**. 
7. Click on **Run crawler** and wait for the State to update to `Completed`. 


## 9. Verifying that the data can be queried on Amazon Athena
This section serves as the verification and validation of the data ingestion and cataloging processes that have been set up in the previous sections. By following these steps, users can ensure that the clickstream data, which has been ingested, processed, and cataloged in AWS Glue, is queryable in Amazon Athena. This verification step validates the end-to-end data pipeline, from data ingestion and storage to query execution, ensuring that the data is readily available for analysis and reporting purposes. It provides confidence in the data's accessibility and usability for further insights and analytics, serving as a crucial quality assurance step in the data processing workflow.

1. On the left panel of AWS Glue, click on **Tables**.  
2. Click on **Table data** for the table name `clickstream_data`. A prompt will appear, click on **Proceed**. 
3. **Run** the query and the results of the `clickstream_data` table appears.

	![img16](/images/img16.png)

## 10. Join tables from 2 sources
This section provide instructions for joining tables from two different sources and cataloging the newly joined table. These steps are essential for integrating data from two separate datasets, the WordPress MySQL database, and the clickstream data, enabling users to combine and analyze information from both sources in a unified manner.

### 10.1 Create an Endpoint storage for the Joint Data
These steps ensures that the output of the join operation has a designated storage location, making it accessible for further analysis and queries.

1. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
2. Select the `application-migration-s3-processed` bucket.
3. Click on **Create folder**, fill in the following parameter values before clicking on **Create folder**.

	| Parameter | Values |
	| ------------- |-------------|
	| Folder name | joint-tables |

### 10.2 Use AWS Glue Job to Join the tables
1. In the S3 processed bucket, we now have data from both the MySQL (`wordpress-db`) and the clickstream data (`clickstream-data`). 
2. We will use AWS Glue Job once again to join 2 tables together, specifically tables `wp_woocommerce_order_items` and `clickstream_data`. 
3. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
4. On the left panel, click on **ETL jobs**, select **Visual with a source and target** then click on **Create**.
5. In total, there will be 7 nodes that will need to be configured.To add the various nodes, click on the **+** button for the transform, source data and target data. 
	1. Source 1: Wordpress data source from Data catalog. 
		1. Select `Data` > `Sources` > `AWS Glue Data Catalog` as the Source, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | AWS Glue Data Catalog - 1 |
			| Database | wordpress-db |
			| Table | wp_woocommerce_order_items |
	2. Source 2: Clickstream data source from Data catalog. 
		1. Select `Data` > `Sources` > `AWS Glue Data Catalog` as the Source, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | AWS Glue Data Catalog - 2 |
			| Database | wordpress-db |
			| Table | clickstream_data |
	3. Change Schema for Source 1
		1. Select `Transforms` > `Change Schema`, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | Change Schema - 1 |
			| Node parents | AWS Glue Data Catalog - 1 |
		2. For the Change Schema section, check the drop column for `Source key: col0`.
		3. Ensure that the Data type for `Source key: col1` is `int`.
	4. Change Schema for Source 2
		1. Select `Transforms` > `Change Schema`, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | Change Schema - 2 |
			| Node parents | AWS Glue Data Catalog - 2 |
		2. For the Change Schema section, check the drop column for `Source key: partition_0`, `partition_1`, `partition_2`, `partition_3`.
		3. Ensure that the Data type for `Source key: productid` is `int`.
	5. Join 2 Nodes together
		1. Select `Transforms` > `Join`, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | Join |
			| Node parents | Change Schema - 1; Change Schema - 2 |
			| Join type | Inner join |
		2. Ensure that the Join conditions is configured to `Change Schema - 1 col1 = Change Schema - 2 productid`.
	6. Change Schema for the Join Node
		1. Select `Transforms` > `Change Schema`, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | Change Schema - 3 |
			| Node parents | Join |
	7. Output Destination: To the S3 bucket.
		1. Select `Data` > `Targets` > `Amazon S3`, and use the following parameter values.
		
	  		| Parameter | Values |
			| ------------- |-------------|
			| Name | S3 bucket |
			| Node parents | Change Schema - 3 |
			| Format | Parquet |
			| Compression Type | Snappy |
			| S3 Target Location | s3://application-migration-s3-processed/joint-tables/ |
6. Click on the **Job details** tab and fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Name | Job 3 - Join Tables |
	| IAM Role | Glue_Job_Role |
	| Worker type | G 8X |
7. Click on **Save** and then **Run**. 
8. When the Glue Job is completed, the Run status will be updated as `Succeeded`. 


### 10.3 Configure AWS Glue Crawler to Catalog the newly Joint Tables
The AWS Glue Crawler is configured again to catalog the newly joined table. Cataloging is essential for making the joined data discoverable and queryable using tools like Amazon Athena or Redshift. This ensures that users can access and analyze the integrated data seamlessly, enabling them to derive meaningful insights from the combined dataset.

1. Go to [AWS Glue on the console](https://console.aws.amazon.com/glue/). 
2. On the left panel, click on **Crawlers**. 
3. Select the existing `wordpress-db-crawler`, click **Action** followed by **Edit crawler**.
4. Click the **Edit** button next to Step 2: Choose data sources and classifiers.
5. Click **Add a data source** and fill in the following parameter values before clicking on **Add an S3 data source**.

	| Parameter | Values |
	| ------------- |-------------|
	| S3 path | s3://application-migration-s3-processed/joint-tables/ |
6. Click **Next** three times followed by **Update**. 
7. Click on **Run crawler** and wait for the State to update to `Completed`. 


## 11. Configuring the database to Redshift

This section provides instructions for configuring a database in Amazon Redshift. This section is necessary to set up a data warehousing solution that can efficiently store and manage large datasets, making it suitable for analytical purposes. This configuration enables the loading and querying of data from various sources, including the previously joined datasets, facilitating complex analytics and reporting tasks. 

![img17](/images/img17.png)

1. Go to [Amazon Redshift on the console](https://console.aws.amazon.com/redshiftv2/).
2. On the left panel, click on **Provisioned clusters dashboard**, then **Create cluster**. 
3. Fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Cluster identifier | redshift-cluster-1 |
	| Node type | dc2.large |
	| Number of nodes | 1 |
	| Admin user name | root |
	| Admin user password | \<password> | 
	
	Remember to change the `<password>` placeholder with your own. 

4. Click on **Manage IAM roles**, then **Create IAM role**. 
5. Select **Any S3 bucket** and click **Create IAM role as default**. 
6. Click **Create cluster**. It should take under 5 minutes for the status to be updated as `Available`.
7. While waiting for the Redshift cluster to be provisioned, go to [IAM on the console](https://console.aws.amazon.com/iamv2/).
8. On the left panel, select **Roles**. Click on the Role Name: `AmazonRedshift-CommandsAccessRole`. 
9. Select **Add permissions** > **Attach policies**.
10. Search and add the policy: `AWSGlueServiceRole`. 
11. Click **Add permissions**. 
12. Next, click on **Query data**. Select the `redshift-cluster-1`.
13. Fill in the following parameter values before clicking on **Create connection**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Authentication | Database user name and password |
	| Database | dev |
	| User name | root |
	| Password | \<password> |
	
	Remember to change the `<password>` placeholder with your own. 

14. Click on **Create** > **Schema**. Fill in the following parameter values before clicking on **Create schema**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Schema | glue-data-catalog |
	| Schema type | External |
	| Glue database name | wordpress-db |
	| IAM role | \<select the AmazonRedshift-CommandAccessRole> |
15. Expand `dev` > `glue-data-catalog` > `Tables`. You should be able to see all the glue data catalog tables now.
16. Double click on the `wp_comments` table and **Run** the query, you will be able to see the data in the table. You can also run more complex queries too. 
17. As the `joint_tables` have nested data, a `View` will need to be created before the data can be used on QuickSight. 
18. Run the following query:
	```
	CREATE VIEW joint_tables AS
	SELECT c.col1, c.col2, c.col3, c.col4, c.productid, c.productname, c.department, c.price, c.productdetails.color, c.productdetails.material, c.productdetails.comments
	FROM "dev"."glue-data-catalog"."joint_tables" c
	WITH NO SCHEMA binding;
	```
	For tips on how to query nested data with Amazon Redshift Spectrum, please refer to this [documentation](https://docs.aws.amazon.com/redshift/latest/dg/tutorial-query-nested-data.html). 

## 12. Configuring the Redshift database to QuickSight
The company's management and analysts required swift insights and chose Amazon QuickSight, a robust data visualization and business intelligence tool. Using it, they developed interactive dashboards and reports for real-time insights into sales trends, customer preferences, and inventory management. This section offers guidance on configuring an Amazon Redshift database to seamlessly integrate with Amazon QuickSight.

![img18](/images/img18.png)

### 12.1 Redshift Settings
This section aims to enable public accessibility and defining inbound rules for the security group ensure that QuickSight can establish a connection to the Redshift cluster for data retrieval.

1. Go to [Amazon Redshift on the console](https://console.aws.amazon.com/redshiftv2/). Click on **redshift-cluster-1**. Click on the **Properties** Tab. 
2. Under the Network and security settings, click on the **Edit** button. 
3. Enable Turn on Publicly accessible. Then click **Save**.
4. Under the Network and security settings, click on the VPC security group attached to the cluster. 
5. Click on the Security group ID > **Edit inbound rules** > **Add rule**. 
6. Fill in the following parameter values before clicking **Save rules**.

	| Parameter | Values |
	| ------------- |-------------|
	| Type | Custom TCP |
	| Port range | 5439 | 
	| Source | 54.70.204.128/27 |
	
	Note: If you had set up the Redshift cluster in another region, kindly click on this [link](https://docs.aws.amazon.com/quicksight/latest/user/regions.html) to find your region IP address range. 

### 12.2 Setting up QuickSight
In the QuickSight setup, users will create an account and configure necessary settings such as authentication method, region selection, and IAM role. This step is essential for QuickSight to communicate with other AWS services, including Redshift.The established link between QuickSight and the Redshift cluster, allows users to perform data analysis directly on Redshift data.

1. Go to [QuickSight on the console](https://quicksight.aws.amazon.com/).
2. Click on **Sign up for QuickSight**. Select Enterprise > **Continue** > **Yes**.
3. Fill in the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Authentication method | Use IAM federated identities & QuickSight-managed users |
	| Select a region | US West (Oregon) |
	| QuickSight account name | root |
	| Notification email address | \<your own email> |
	| IAM Role | Use QuickSight-managed role (default) |
	
	Remember to change the `<your own email>` placeholder with your own. 

4. Enable access for Amazon S3 > **Select all** > **Finish**. 
5. Upon successful creation of the account, you should be able to see the following screenshot.
6. Click on **Go to Amazon QuickSight** > **New analysis** > **New dataset** > **Redshift Auto-discovered**. 
7. Fill in the following parameter values before clicking on **Create data source**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Data source name | redshift-datasource |
	| Instance ID | redshift-cluster-1 |
	| Connection type | Public network |
	| Database name | dev |
	| Username | root |
	| Password | \<your Redshift cluster password> |
8. Select `public` as the Schema. Select the `joint_tables` table to visualize. Click on **Visualise**, then **Create**.

### 12.3 Visualising on QuickSight
This visual representation helps users gain insights from the data. Furthermore, these visualizations and dashboards can be made accessible to other users for collaborative data analysis and decision-making. 

1. Under Visual types, select the **Word Cloud** option and drag `department` into Group by and `produced` into Size. The graph with the largest word shows the department with the most product. 

![img19](/images/img19.png)

2. On the top right hand corner, click the **save icon** and save the name as `department analysis`. 
3. On the top right hand corner, click on the **share icon** to publish the dashboard as `department dashboard`. 
4. To share the dashboard with other users, on the top right hand corner, click on the **person icon**, then **Manage QuickSight**. Click on **Invite users** and enter the email address of the people you want to share with. 
5. With that, we have achieved setting up an end-to-end data analysis and visualization pipeline. 
