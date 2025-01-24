import boto3
from datetime import datetime, timedelta, timezone
from openpyxl import Workbook
COST_PER_GB = 0.023
OUTBOUND_DATA_COST = 0.09
REQUEST_COST = 0.005

S3_client=boto3.client('s3')

def bucket_location(bucket_name):
    response1 = S3_client.get_bucket_location(Bucket=bucket_name)
    region = response1.get('LocationConstraint') or "us-east-1"
    return region

def bucket_size(bucket_name):
    total_size = 0
    try:
        response = S3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                total_size += obj['Size']  # Sum up the sizes of all objects in the bucket
              # Convert bytes to MB
            
    except Exception as e:
        return 0
    size_in_mb = total_size / (1024 * 1024)
    size_in_gb = total_size / (1024 * 1024 * 1024)  # Convert bytes to GB
    return size_in_mb , size_in_gb

def bucket_cost(bucket_name):
    _, size_in_gb = bucket_size(bucket_name)
    return size_in_gb * COST_PER_GB  # Calculate the storage cost


def bucket_unused(bucket_name, days=20):
    try:
        response = S3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            return True
        #cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)  # Ensure timezone-aware datetime
        for obj in response['Contents']:
            if obj['LastModified'] > cutoff_date:
                return False
        return True
    except Exception as e:
        return False

def list_of_buckets():
     # Initialize the workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "S3 Bucket Report"

    # Add headers to the Excel file
    headers = ["Bucket Name", "Location", "Size (MB)", "Unused (20 days)", "Can be Cleanup", "Cost of Storage(in USD)"]
    ws.append(headers)

    respose= S3_client.list_buckets()
    list_of_bucket=[]
    for bucket in respose['Buckets']:
        bucket_name=bucket['Name']
        bucketlocation=bucket_location(bucket_name)
        #bucketsize=bucket_size(bucket_name)
        bucketsize_mb, bucketsize_gb = bucket_size(bucket_name)
        is_unused = bucket_unused(bucket_name, 20)
        #print(f"bucket Name {bucket_name} and location is {bucketlocation} and its size is {bucketsize}")
        bucket_unused(bucket_name,20)

        # Determine if the bucket is unused and size > 10MB
        condition_met = "Yes" if (bucketsize_mb > 10 and is_unused) or (bucketsize_mb == 0)  else "No"
        storage_cost = bucket_cost(bucket_name)  # Calculate cost

        # Append data to Excel file
        ws.append([bucket_name, bucketlocation, round(bucketsize_mb, 2), is_unused, condition_met, round(storage_cost, 2)])
        
        '''if bucketsize > 10 and is_unused:
            return 'yes'
            #list_of_bucket.append(bucket_name)
        else:
            return 'no'
            '''
        
    # Save the Excel file
    report_name = "S3_Bucket_Report.xlsx"
    wb.save(report_name)

    print(f"\nExcel report saved as {report_name}")
    print("\nBuckets unused for 20 days and larger than 10 MB:", is_unused)

    print(list_of_bucket)

list_of_buckets()
#bucket_location()