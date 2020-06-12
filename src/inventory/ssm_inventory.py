#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 12:56:06 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Thursday, June 11th 2020, 4:23:32 pm
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
instances = []


def handler(profile, region):
    global s
    s = awsume(profile) 
    regions = [region] if region else get_regions('ssm')  
    
    with ThreadPool(processes=5) as pool:
        t = pool.map(get_ssm_inventory, regions)
    return pd.DataFrame(instances)  



def get_ssm_inventory(region, tries=1):
    account_id = get_account_id(s)
    account_name = get_account_name(s)
    try: 
        ssm = s.client('ssm', region_name=region)
        paginator = ssm.get_paginator('describe_instance_information')
        print(f'Processing SSM inventory data from {account_name} {account_id} in {region}')
        for res in paginator.paginate():
            for instance in res['InstanceInformationList']:
                _instance = {}
                _instance['AccountName'] = account_name
                _instance['AccountId'] = account_id
                _instance['Region'] = region
                _instance['InstanceId'] = instance['InstanceId']
                # _instance['ComputerName'] = instance['ComputerName']
                _instance['PlatformType'] = instance['PlatformType']
                _instance['PlatformType'] = ''
                try:
                    _instance['PlatformType'] = instance['PlatformType']
                except:
                    pass
                _instance['PlatformVersion'] = ''
                try:
                    _instance['PlatformVersion'] = instance['PlatformVersion']
                except:
                    pass
                _instance['SSMAgentVersion'] = instance['AgentVersion']
                _instance['IsLatestVersion'] = instance['IsLatestVersion']
                _instance['PingStatus'] = instance['PingStatus']
                # ValueError: Excel does not support datetimes with timezones. Please ensure that datetimes are timezone unaware before writing to Excel.
                # Need to convert and then strip
                _instance['LastPingDateTime'] = utc_to_nzst(instance['LastPingDateTime']).replace(tzinfo=None) 
                _instance['IPAddress'] = instance['IPAddress']
                global instances
                instances.append(_instance)

    except ClientError as e:
        if tries <= 3:
            print(f'Throttling Exception Occurred. Retrying ...  {account_name} {account_id} in {region}... Attempt No.: {tries}')
            time.sleep(3)   # Sleeps the thread, not process
            return get_ssm_inventory(region, tries+1)
        else:
            raise ValueError('Attempted 3 Times But No Success. Raising Exception...')




