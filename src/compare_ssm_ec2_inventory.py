#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 6:55:49 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, June 9th 2020, 9:06:32 am
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
    
    # print(ssm_inventory.shape)
    # print(ec2_inventory.shape)
    # df = merge_platform_type(ssm_inventory, ec2_inventory)
    df = pd.merge(ssm_inventory.drop(columns=['AccountName', 'AccountId', 'Region']), ec2_inventory, on='InstanceId', how='outer')

    # df = df.drop_duplicates(subset=['PlatformType_x', 'PlatformType_y'], keep='last')
    # df = pd.merge(df, df2.set_index('UserID'), left_on='UserName', right_index=True)
    df = df.rename(columns = {'PlatformType_x':'PlatformType'})
    df = df.sort_values('State')
    return df



def merge_platform_type(ssm, ec2):
    # print(ssm.to_string())
    # print(ec2.to_string())
    return pd.merge(ssm, ec2, on='PlatformType', how='inner')

    # df = pd.merge(ssm, ec2.set_index('PlatformType'), left_on='', right_index=True)