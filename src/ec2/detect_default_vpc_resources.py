#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Tuesday, July 7th 2020, 1:01:20 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, July 7th 2020, 1:08:35 pm
###

import boto3
import pandas as pd
from awsume.awsumepy import awsume
from botocore.exceptions import ClientError
from multiprocessing.pool import ThreadPool

from src.utils import (
    get_account_id,
    get_account_name,
    get_regions,
    utc_to_nzst
)

s = boto3.session.Session()
resources = []

def handler(profile, region):
    '''
    Detects dependent resources in VPC
    '''
    global s
    s = awsume(profile)

    print("\nDeleting default VPCs from {}...\n".format(profile))

    regions = [region] if region else get_regions('ec2')  

    with ThreadPool(processes=5) as pool:
        t = pool.map(detect_DefaultVPC_resources, regions)
    
    return pd.DataFrame()


def detect_DefaultVPC_resources():
    ec2 = s.client('ec2')
    res = ec2.describe_vpcs()
    default_vpc_id = [vpc['VpcId'] for vpc in res['Vpcs'] if vpc['IsDefault']]
    if not default_vpc_id:
        return
         
    res = ec2.describe_network_interfaces(Filters=[{'Name': 'vpc-id', 'Values': default_vpc_id}])
    if res['NetworkInterfaces']:
        for eni in res['NetworkInterfaces']:
            if eni['Description']:
                descrip = eni['Description']
            else:
                descrip =f"Type: {eni['InterfaceType']} Id: {eni['Attachment']['InstanceId']}"
            print(f"Dependent Resource in DefaultVPC: {descrip} in region {eni['AvailabilityZone']}")
            
            _resource = {}
            _resource['PrerequisiteCheck'] = f'Default VPC Dependent Resource'
            _resource['Reason'] = 'Control Tower removes DefaultVPC as part of its baseline process.'
            _resource['Detail'] = 'Cannot delete Default VPC if there are dependent resources.'
            _resource['Region'] = eni['AvailabilityZone']
            _resource['ResourceName'] = descrip
            _resource['Arn'] =  eni['NetworkInterfaceId']
            _resource['DependentResources'] = json.dumps(eni, default=str)
            resources.append(_resource)