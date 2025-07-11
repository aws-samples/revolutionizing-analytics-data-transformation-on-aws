# MySQL data to S3 using Amazon Kinesis

## Reference Architecture

![img20](/images/img20.png)

This architecture diagram presents an alternative data ingestion approach for transferring data from the MySQL database to the target S3 bucket. By implementing this method, you can bypass the initial setup steps detailed in the README.md Sections 4 and Section 5.

This method is preferred for a few reasons:

1. **Real-time Data Streaming:** Amazon Kinesis Data Streams is a real-time data streaming service. By routing data through Kinesis, you can make your data available for real-time processing and analysis. This is particularly valuable when you need up-to-the-minute insights from your data.
2. **Data Transformation:** Amazon Kinesis Data Firehose can perform data transformations before storing the data in Amazon S3. You can use this to enrich, clean, or reformat the data as it flows through the pipeline. This is especially useful when you need to conform data from various sources into a common format.
3. **Scalability and Resilience:** AWS services like Kinesis are designed to handle large volumes of data and are highly scalable and resilient. They can automatically handle load spikes, fault tolerance, and data partitioning, ensuring that your data pipeline can accommodate growing data volumes.
4. **Cost Optimization:** Depending on your usage patterns, this workflow can help optimize costs. For example, Kinesis Data Firehose can batch and compress data before writing it to S3, reducing storage and data transfer costs.

Overall, this workflow offers a robust, scalable, and flexible way to move data from a MySQL database to Amazon S3, while also providing real-time streaming capabilities and data transformation options. It's a powerful solution for organizations looking to centralize and make the most of their data, especially when dealing with large volumes and real-time data requirements.


## 1. Setting up the Kinesis Ingestion Pipeline to the Target S3 Bucket
In this section, we will be creating an S3 bucket and its permission for the MySQL database to be stored in the AWS Cloud after the migration. 

### 1.1 Create the Target S3 Bucket
1. Go to [S3 on the console](https://s3.console.aws.amazon.com/s3/).
2. Click on **Create Bucket**, fill the following parameter values and replace `<add your bucket name here>` before clicking on **Create bucket**. 

	| Parameter | Values |
	| ------------- |-------------|
	| Bucket name | \<add your bucket name here> |
	| AWS Region | US West (Oregon) us-west-2 |

3. Select the `<add your bucket name here>` bucket.
4. Click on **Create folder**. Fill in the following parameter values before clicking on **Create folder**.

	| Parameter | Values |
	| ------------- |-------------|
	| Folder name | wordpress-db |

### 1.2 Create the Role for DMS to access the Target Kinesis
This section involves creating a role that allows AWS Database Migration Service (DMS) to access and interact with the target Kinesis. 

1. Go to [Identity and Access Management (IAM) on the console](https://console.aws.amazon.com/iamv2/). 
2. On the left panel, select `Roles`, followed by **Create role**. 
3. Enter the following parameter values. 

	| Parameter | Values |
	| ------------- |-------------|
	| Trusted entity type | AWS service |
	| Use cases for other AWS services: | DMS |
4. Select the radio button for `DMS` and click **Next**. 
5. In the search field for the Permission policies, search for this policy `AmazonKinesisFullAccess`, select the policy and then choose **next**. 
6. Fill in the role name as `DMS_to_Kinesis_role`, followed by **Create role**. 
7. Once created, copy the ARN of that role, `arn:aws:iam::<AWS account ID>:policy/DMS_to_Kinesis_role`, and keep it for use in Section 5.4 Configure the Target Endpoint.

### 1.3 Configuring Amazon Kinesis Data Stream
1. Go to [Kinesis on the console](https://console.aws.amazon.com/kinesis/).
2. Click on **Create data stream**. Fill in the following parameter values before clicking on **Create data stream**.

	| Parameter | Values |
	| ------------- |-------------|
	| Data stream name | kds-mysql-data |
	| Capacity mode | On-demand |
3. Once provisioned, the Status should update to `Active`.

### 1.4 Configuring Amazon Kinesis Data Firehose
The MySQL data from the Kinesis Data Stream will be input to the Kinesis Data Firehose before the data lands in the S3 bucket. 

1. On the left panel, click on **Data Firehose**. 
2. Click on **Create delivery stream**. Fill in the following parameter values before clicking on **Create delivery stream**.

	| Parameter | Values |
	| ------------- |-------------|
	| Source | Amazon Kinesis Data Streams |
	| Destination | Amazon S3 |
	| Kinesis data stream | \<click Browse and select kds-mysql-data> |
	| Delivery stream name | kdf-mysql-data |
	| S3 bucket destination | s3://\<add your bucket name here> |
	| S3 bucket prefix | wordpress-db/ |
	| Buffer size | 1 MiB |
	| Buffer interval | 60 seconds | 
3. Once provisioned, the Status should update to `Active`.


## 2. Setting up Database Migration Service (DMS)
This section provides a comprehensive guide to setting up and configuring the components of the Database Migration Service (DMS) for the migration process. 

### 2.1 Configure the Subnet Group
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

### 2.2 Configure the Replication Instance
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

### 2.3 Configure the Source Endpoint
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

	Remember to change the `<password>` and `<string-of-numbers>` placeholder with your own. The Server name can be obtained from [Cloudformation](https://us-west-2.console.aws.amazon.com/cloudformation/) Stack under `Outputs`, DBServerDNSName.  
	
	![img7](/images/img7.png)

4. Expand the `Test endpoint connection (optional)` section. 
5. Select the following parameter values and click **Run test**. 

	| Parameter | Values |
	| ------------- |-------------|
	| VPC | TargetVPC |
	| Replication instance | replication-instance |
6. After a minute, the Status should indicate `successful`, thereafter, proceed to click on  **Create endpoint**. 

### 2.4 Configure the Target Endpoint
1. Go to [AWS Database Migration Service on the console](https://console.aws.amazon.com/dms/v2/). 
2. Click on `Endpoints` followed by **Create endpoint**. 
3. Enter the following parameter values. If the parameter is not mentioned in the table, always leave it to the default value. 

	| Parameter | Values |
	| ------------- |-------------|
	| Endpoint type | Target endpoint |
	| Endpoint identifier | target-endpoint |
	| Source engine | Amazon Kinesis |
	| Amazon Resource Name (ARN) for service access role | arn:aws:iam::\<AWS account ID>:policy/DMS_to_Kinesis_role |
	| Kinesis Stream ARN | arn:aws:kinesis:us-west-2:\<AWS account ID>:stream/kds-mysql-data |
	| Message format | JSON |

	The Amazon Resource Name (ARN) for service access role can be obtained from Section 4.2. 

5. Expand the `Test endpoint connection (optional)` section. 
6. Select the following parameter values and click on **Run test**. 

	| Parameter | Values |
	| ------------- |-------------|
	| VPC | TargetVPC |
	| Replication instance | replication-instance |
7. After a minute, the Status should indicate `successful`, thereafter, proceed to click on **Create endpoint**. 


### 2.5 Configure the Database Replication Task
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
