import boto3
import pandas as pd
from awsume.awsumepy import awsume

from src.utils import (
    get_account_id,
    get_account_name,
    get_regions,
    utc_to_nzst
)

s = boto3.session.Session()

def handler(profile, region):
    '''
    deletes default VPCs from all regions
    '''
    global s
    s = awsume(profile)

    print("This script will delete default VPCs with the CIDR block 172.31.0.0/16 (and it's associated resources)")

    user_confirmation = input("\nAre you sure you want to deploy delete default VPCs onto {} (Y/N): ".format(profile))
    if user_confirmation.lower() != 'y':
        print("Exiting script. No VPCs deleted.")
         # doesn't return an output
        return pd.DataFrame()

    print("\nDeleting default VPCs from {}...\n".format(profile))

    regions = [region] if region else get_regions('ec2')  

    vpcs_deleted = 0
    for region in regions:
        print("Region = " + region)
        vpcs_deleted += delete_default_vpc(region)

    print("\n" + str(vpcs_deleted) + " default VPCs deleted from {}".format(profile))

    # Currently doesn't return an output
    return pd.DataFrame()


def delete_default_vpc(region):
    '''
    deletes the default VPC from the client region
    '''
    client = s.client('ec2', region_name=region)
    resource = s.resource('ec2', region_name=region)
    vpc_list = client.describe_vpcs()['Vpcs']

    deletion_count = 0
    for vpc in vpc_list:
        if vpc['CidrBlock'] == '172.31.0.0/16':
            print("    Deleting " + vpc['VpcId'])
            try:
                vpcResource = resource.Vpc(vpc['VpcId'])
                
                delete_vpc_resources(vpcResource, vpc['VpcId'], client, resource)

                client.delete_vpc(VpcId=vpc['VpcId'], DryRun=False)
                deletion_count += 1
            except Exception as deletion_exception:
                print(deletion_exception)
                pass

    return deletion_count


def delete_vpc_resources(vpc, vpcid, client, resource):
    for gw in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=gw.id)
        gw.delete()
    # delete all route table associations
    for rt in vpc.route_tables.all():
        for rta in rt.associations:
            if not rta.main:
                rta.delete()
    # delete any instances
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            instance.terminate()
    # delete our endpoints
    for ep in client.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
    # delete our security groups
    for sg in vpc.security_groups.all():
        if sg.group_name != 'default':
            sg.delete()
    # delete any vpc peering connections
    for vpcpeer in client.describe_vpc_peering_connections(
            Filters=[{
                'Name': 'requester-vpc-info.vpc-id',
                'Values': [vpcid]
            }])['VpcPeeringConnections']:
        resource.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()
    # delete non-default network acls
    for netacl in vpc.network_acls.all():
        if not netacl.is_default:
            netacl.delete()
    # delete network interfaces
    for subnet in vpc.subnets.all():
        for interface in subnet.network_interfaces.all():
            interface.delete()
        subnet.delete()
