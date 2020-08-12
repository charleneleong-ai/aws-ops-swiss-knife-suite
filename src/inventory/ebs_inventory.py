#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Wednesday, August 12th 2020, 10:12:12 am
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Wednesday, August 12th 2020, 3:32:58 pm
###

import os
import json
import boto3
from botocore.exceptions import ClientError
from multiprocessing.pool import ThreadPool
import time

import pandas as pd
from awsume.awsumepy import awsume

from src.utils import (
    get_account_id,
    get_account_name,
    get_regions,
    utc_to_nzst
)

s = boto3.session.Session()
volumes = []

def handler(profile, region):
    global s
    s = awsume(profile)
    regions = [region] if region else get_regions('ec2')  

    with ThreadPool(processes=5) as pool:
        t = pool.map(get_ebs_inventory, regions)

    return pd.DataFrame(volumes)  
    
     

def get_ebs_inventory(region, tries=1):
    account_id = get_account_id(s)
    account_name = get_account_name(s)
    try: 
        volumes_list = describe_volumes(region)
        print(f'Processing EBS inventory data from {account_name} {account_id} in {region}')

        for vol in volumes_list:
            _vol= {}
            _vol['AccountName'] = account_name
            _vol['AccountId'] = account_id
            _vol['Region'] = region
            _vol['AvailabilityZone'] = vol['AvailabilityZone']
            try:
                instances = [attachments['InstanceId'] for attachments in vol['Attachments']]
                _vol['Attachments'] = ', '.join(instances)
                hostnames = [get_ec2_hostname(instance_id, region) for instance_id in instances]
                _vol['Hostnames'] = ', '.join(hostnames)
            except:
                _vol['Attachments'] = ''
                _vol['Hostnames'] = ''
            _vol['VolumeId'] = vol['VolumeId']
            _vol['Encrypted'] = vol['Encrypted']
            try: 
                _vol['KmsKeyId'] = vol['KmsKeyId']
            except:
                _vol['KmsKeyId'] = ''
            _vol['Size'] = vol['Size']
            _vol['SnapshotId'] = vol['SnapshotId']
            try: 
                _vol['Iops'] = vol['Iops']
            except:
                _vol['Iops'] = ''
            _vol['State'] =  vol['State']
            global volumes
            volumes.append(_vol)
                
    except ClientError as e:
        if tries <= 3:
            print(f'Throttling Exception Occurred. Retrying ...  {account_name} {account_id} in {region}... Attempt No.: {tries}')
            time.sleep(3)   # Sleeps the thread, not process
            return get_ebs_inventory(region, tries+1)
        else:
            raise ValueError('Attempted 3 Times But No Success. Raising Exception...')


def describe_volumes(region):
    ec2 = s.client('ec2', region_name=region)
    paginator = ec2.get_paginator('describe_volumes')

    volumes = []
    for res in paginator.paginate():
        for vol in res['Volumes']:
            volumes.append(vol)
    return volumes


def get_ec2_hostname(instance_id, region):
    ec2 = s.client('ec2', region_name=region)
    tags = ec2.describe_tags(Filters=[{'Name':'resource-id', 'Values':[instance_id]}])['Tags']
    for tag in tags:
        if tag['Key']=='Name':
            return tag['Value']