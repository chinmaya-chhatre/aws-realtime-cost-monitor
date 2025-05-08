import boto3  # AWS SDK for Python to interact with AWS services
import csv  # For writing the output to a CSV file
import logging  # For logging info, errors, and debug statements
from datetime import datetime  # To handle dates
from calendar import monthrange  # To calculate the number of days in the current month

# Configure logging: logs both to a file and console for visibility
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("aws_cost_prediction.log"),
        logging.StreamHandler()
    ]
)

# Initialize AWS service clients
ec2 = boto3.client("ec2")
cost_explorer = boto3.client("ce")

# Calculate date ranges
start_of_month = datetime(datetime.today().year, datetime.today().month, 1)
current_date = datetime.today()
days_in_month = monthrange(current_date.year, current_date.month)[1]
remaining_days = max(days_in_month - current_date.day, 0)

logging.info(f"Start of Month: {start_of_month.strftime('%Y-%m-%d')}")
logging.info(f"Current Date: {current_date.strftime('%Y-%m-%d')}")
logging.info(f"Days in Month: {days_in_month}, Remaining Days: {remaining_days}")

def get_service_cost(service_name):
    """
    Fetches the total cost incurred so far this month for a specific AWS service
    using the Cost Explorer API.

    :param service_name: The full name of the AWS service (e.g., "Amazon S3").
    :return: Float value of total cost.
    """
    try:
        logging.info(f"Fetching cost for {service_name} from AWS Cost Explorer...")
        
        # Use Cost Explorer to get cost data for the current month
        response = cost_explorer.get_cost_and_usage(
            TimePeriod={
                "Start": start_of_month.strftime("%Y-%m-%d"),
                "End": current_date.strftime("%Y-%m-%d")
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            Filter={
                "Dimensions": {"Key": "SERVICE", "Values": [service_name]}
            },
        )
        
        # Extract cost from response
        cost = float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
        logging.info(f"{service_name} Cost: ${cost}")
        
        return round(cost, 4)
    except Exception as e:
        logging.error(f"Error fetching {service_name} cost: {e}")
        return 0.0

def get_ec2_instances(region):
    """
    Retrieves details of EC2 instances in a specific region, including their type,
    status, and calculates both accrued and predicted costs.

    :param region: AWS region name (e.g., 'us-east-1').
    :return: List of EC2 instance cost details.
    """
    ec2_client = boto3.client("ec2", region_name=region)
    instances = ec2_client.describe_instances()
    ec2_data = []

    logging.info(f"Fetching EC2 instances for {region}...")

    # Loop through all reservations and instances
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            state = instance["State"]["Name"]

            # NOTE: Replace this with real pricing API for production use
            price_per_hour = 0.0116 if instance_type == "t2.micro" else 0.1216  
            
            # Calculate costs: accrued (so far) and full-month predicted
            accrued_cost = round(price_per_hour * (current_date.day * 24), 4) if state == "running" else 0
            predicted_cost = round(price_per_hour * days_in_month * 24, 4)

            logging.info(
                f"EC2 Instance {instance_id} ({instance_type}) - "
                f"State: {state} - ${price_per_hour}/hr - "
                f"Accrued: ${accrued_cost} - Predicted: ${predicted_cost}"
            )

            ec2_data.append([
                "EC2",
                region,
                instance_id,
                instance_type,
                state,
                price_per_hour,
                accrued_cost,
                predicted_cost
            ])
    return ec2_data

def get_all_regions():
    """
    Retrieves all available AWS regions.
    
    :return: List of region names (e.g., ['us-east-1', 'us-west-2']).
    """
    return [region["RegionName"] for region in ec2.describe_regions()["Regions"]]

def write_to_csv(data):
    """
    Writes the collected AWS resource cost data to a CSV file.

    :param data: List of cost details (each as a list of fields).
    """
    with open("aws_cost_prediction.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Service",
            "Region",
            "Resource ID",
            "Type",
            "State",
            "Price Per Hour",
            "Accrued Cost",
            "Predicted Cost"
        ])
        writer.writerows(data)
    logging.info("Cost prediction data saved to 'aws_cost_prediction.csv'")

def main():
    """
    Main function that orchestrates AWS cost retrieval for various services and writes results.
    """
    logging.info("Fetching data for all AWS regions...")
    all_regions = get_all_regions()
    all_data = []

    # Process EC2 data across all regions
    for region in all_regions:
        logging.info(f"Fetching data for region: {region}...")
        all_data.extend(get_ec2_instances(region))

    # Fetch S3 costs as a whole (no region-specific cost breakdown)
    s3_cost = get_service_cost("Amazon Simple Storage Service (S3)")
    all_data.append([
        "S3",
        "All Regions",
        "N/A",
        "Active",
        "Active",
        0,
        s3_cost,
        s3_cost
    ])

    # Write all results to CSV
    write_to_csv(all_data)

    logging.info("Cost prediction process completed.")

# Run the script if this file is executed directly
if __name__ == "__main__":
    main()
