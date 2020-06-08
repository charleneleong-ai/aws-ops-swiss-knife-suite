#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 5:18:14 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Monday, June 8th 2020, 7:40:33 pm
###

import os
import json
import boto3
from botocore.exceptions import ClientError
from multiprocessing.pool import ThreadPool
import time

import pandas as pd
from awsume.awsumepy import awsume

from utils import get_account_id, get_account_name, utc_to_nzst, get_regions

s = boto3.session.Session()
instances = []

def handler(profile, region):
    global s
    s = awsume(profile)
    regions = [region] if region else get_regions('ec2')  

    with ThreadPool(processes=5) as pool:
        t = pool.map(get_ec2_inventory, regions)
    return pd.DataFrame(instances)  
    
     

def get_ec2_inventory(region, tries=1):
    account_id = get_account_id()
    account_name = get_account_name()
    try: 
        ec2 = s.client('ec2', region_name=region)
        paginator = ec2.get_paginator('describe_instances')

        print(f'Processing EC2 inventory data from {account_name} {account_id} in {region}')
        for res in paginator.paginate():
            for instance in res['Reservations']:
                instance = instance['Instances'][0]
                _instance = {}
                _instance['AccountName'] = account_name
                _instance['AccountId'] = account_id
                _instance['Region'] = region
                _instance['InstanceId'] = instance['InstanceId']
                _instance['PrivateDnsName'] = instance['PrivateDnsName']
                _instance['PublicDnsName'] = instance['PublicDnsName']
                _instance['State'] = instance['State']['Name']
                _instance['PlatformType'] = ''
                try: 
                    _instance['PlatformType'] = instance['Platform'].capitalize()
                except:
                    pass
                _instance['IamInstanceProfile'] = ''
                try: 
                    _instance['IamInstanceProfile'] = instance['IamInstanceProfile']['Arn']
                except:
                    pass
                _instance['InstanceType'] = instance['InstanceType']
                _instance['Tags'] = json.dumps(instance['Tags'], default=str)
                _instance['MonitoringState'] = instance['Monitoring']['State']
                global instances
                instances.append(_instance)
                
    except ClientError as e:
        if tries <= 3:
            print(f'Throttling Exception Occurred. Retrying ...  {account_name} {account_id} in {region}... Attempt No.: {tries}')
            time.sleep(3)   # Sleeps the thread, not process
            return get_ec2_inventory(region, tries+1)
        else:
            raise ValueError('Attempted 3 Times But No Success. Raising Exception...')
