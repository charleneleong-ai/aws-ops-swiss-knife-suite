#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 6:55:49 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, June 9th 2020, 11:43:57 am
###


import os
import json
import boto3
from botocore.exceptions import ClientError
from multiprocessing.pool import ThreadPool
import time

import pandas as pd
from awsume.awsumepy import awsume

from ssm_inventory import handler as ssm_inventory_handler
from ec2_inventory import handler as ec2_inventory_handler
from utils import get_account_id, get_account_name, get_regions, utc_to_nzst


s = boto3.session.Session()


def handler(profile, region):
    global s
    s = awsume(profile) 
    regions = [region] if region else get_regions('ec2')  
    
    ssm_inventory = ssm_inventory_handler(profile, region)
    ec2_inventory = ec2_inventory_handler(profile, region)
    
    
    print(ssm_inventory.shape, ec2_inventory.shape)
    
    if ssm_inventory.shape == (0, 0):   # No instances in SSM
        df = ec2_inventory
    else:
        print(f'Merging SSM and EC2 inventory for {profile} in {region}')
        df = pd.merge(ssm_inventory.drop(columns=['AccountName', 'AccountId', 'Region']), ec2_inventory, on='InstanceId', how='outer')

        ### Need to merge PlatformType cols
        # df['PlatformType'] = df['PlatformType_x'] + df['PlatformType_y']
        # df = df.drop(columns=['PlatformType_x', 'PlatformType_y'])
        df = df.rename(columns = {'PlatformType_x': 'PlatformType'})
        df.drop(columns=['PlatformType_y'])
        
        cols = ['AccountName', 'AccountId', 'Region', 'InstanceId', 'PlatformType', 'State', 
                'IamInstanceProfile', 'PlatformVersion', 'SSMAgentVersion', 'IsLatestVersion', 
                'PingStatus', 'LastPingDateTime', 'IPAddress', 'PrivateDnsName', 'PublicDnsName', 
                'InstanceType', 'Tags', 'MonitoringState']
        df = df[cols]
        
    df = df.sort_values('State')

    return df


