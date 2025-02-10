import boto3
import csv
import logging
from datetime import datetime, timedelta
from calendar import monthrange

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("aws_cost_prediction.log"),
        logging.StreamHandler()
    ]
)

# Initialize AWS clients
ec2 = boto3.client("ec2")
cost_explorer = boto3.client("ce")

# Get the current date and calculate the number of days in the month
start_of_month = datetime(datetime.today().year, datetime.today().month, 1)
current_date = datetime.today()
days_in_month = monthrange(current_date.year, current_date.month)[1]
remaining_days = max(days_in_month - current_date.day, 0)

logging.info(f"Start of Month: {start_of_month.strftime('%Y-%m-%d')}")
logging.info(f"Current Date: {current_date.strftime('%Y-%m-%d')}")
logging.info(f"Days in Month: {days_in_month}, Remaining Days: {remaining_days}")

def get_service_cost(service_name):
    """
    Retrieves the cost of a given AWS service using AWS Cost Explorer.
    :param service_name: Name of the AWS service (e.g., "Amazon Simple Storage Service (S3)").
    :return: The total cost of the service as a float.
    """
    try:
        logging.info(f"Fetching cost for {service_name} from AWS Cost Explorer...")
        response = cost_explorer.get_cost_and_usage(
            TimePeriod={"Start": start_of_month.strftime("%Y-%m-%d"), "End": current_date.strftime("%Y-%m-%d")},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": [service_name]}},
        )
        logging.debug(f"Full AWS Cost Explorer Response: {response}")

        cost = float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
        logging.info(f"{service_name} Cost: ${cost}")
        return round(cost, 4)
    except Exception as e:
        logging.error(f"Error fetching {service_name} cost: {e}")
        return 0.0

def get_ec2_instances(region):
    """
    Retrieves EC2 instance details for a given AWS region.
    :param region: AWS region name.
    :return: List of EC2 instance cost details.
    """
    ec2_client = boto3.client("ec2", region_name=region)
    instances = ec2_client.describe_instances()
    ec2_data = []

    logging.info(f"Fetching EC2 instances for {region}...")

    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            state = instance["State"]["Name"]

            # Example EC2 pricing, adjust based on actual pricing API
            price_per_hour = 0.0116 if instance_type == "t2.micro" else 0.1216  
            accrued_cost = round(price_per_hour * (current_date.day * 24), 4) if state == "running" else 0
            predicted_cost = round(price_per_hour * days_in_month * 24, 4)  # Full-month prediction

            logging.info(f"EC2 Instance {instance_id} ({instance_type}) - State: {state} - ${price_per_hour}/hr - Accrued: ${accrued_cost} - Predicted: ${predicted_cost}")

            ec2_data.append(["EC2", region, instance_id, instance_type, state, price_per_hour, accrued_cost, predicted_cost])
    return ec2_data

def get_all_regions():
    """
    Retrieves all available AWS regions.
    :return: List of AWS region names.
    """
    return [region["RegionName"] for region in ec2.describe_regions()["Regions"]]

def write_to_csv(data):
    """
    Writes the collected AWS resource cost data to a CSV file.
    :param data: List of cost details.
    """
    with open("aws_cost_prediction.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Service", "Region", "Resource ID", "Type", "State", "Price Per Hour", "Accrued Cost", "Predicted Cost"])
        writer.writerows(data)
    logging.info("Cost prediction data saved to 'aws_cost_prediction.csv'")

def main():
    """
    Main function that orchestrates AWS cost retrieval for various services.
    """
    logging.info("Fetching data for all AWS regions...")
    all_regions = get_all_regions()
    all_data = []

    for region in all_regions:
        logging.info(f"Fetching data for region: {region}...")
        all_data.extend(get_ec2_instances(region))

    # Fetching S3 costs
    s3_cost = get_service_cost("Amazon Simple Storage Service (S3)")
    all_data.append(["S3", "All Regions", "N/A", "Active", "Active", 0, s3_cost, s3_cost])

    # Write final data to CSV
    write_to_csv(all_data)

    logging.info("Cost prediction process completed.")

if __name__ == "__main__":
    main()
