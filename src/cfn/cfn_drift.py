#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 12:53:50 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, July 21st 2020, 2:21:32 pm
###

import os
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
resources = []


def handler(profile, region, dryrun):
    global s
    s = awsume(profile)
    global run
    run = dryrun
    
    regions = [region] if region else get_regions('cloudformation')
    for region in regions:
        stack_names = get_stack_names(region)
        detect_cfn_drift_df(stack_names, region)
        
    df = pd.DataFrame(resources)
    df = df.sort_values('StackResourceDriftStatus')
    return df



def get_stack_names(region, tries=1):
    account_name = get_account_name()
    try: 
        cfn = s.client('cloudformation', region_name=region)
        paginator = cfn.get_paginator('list_stacks')
        response_iterator = paginator.paginate(
            StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']
        )
        stack_names = []
        for res in response_iterator:
            for stack in res['StackSummaries']:
                stack_names.append(stack['StackName'])
        print(f'\n{len(stack_names)} stacks found in {account_name} {region}\n===================')
        with ThreadPool(processes=5) as pool:
            t = pool.map(trigger_cfn_detect_drift, stack_names)
            
    except ClientError as e:
        if tries <= 3:
            print(f'Throttling Exception Occurred. Retrying ... {region} ... Attempt No.: {tries}')
            time.sleep(3)   # Sleeps the thread, not process
            return get_stack_names(region, tries+1)
        else:
            raise ValueError('Attempted 3 Times But No Success. Raising Exception...')
    return stack_names



def trigger_cfn_detect_drift(stack_name, tries=1):
    cfn = s.client('cloudformation')
    try: 
        res = cfn.detect_stack_drift(StackName=stack_name)
        if res['ResponseMetadata']['HTTPStatusCode']==200:
            print(f'Successfully triggered drift detection on {stack_name}')
    except ClientError as e:
        if tries <= 3:
            print(f'Throttling Exception Occurred. Retrying ...  {stack_name} ... Attempt No.: {tries}')
            time.sleep(3)   # Sleeps the thread, not process
            return trigger_cfn_detect_drift(stack_name, tries+1)
        else:
            raise ValueError('Attempted 3 Times But No Success. Raising Exception...')



def detect_cfn_drift_df(stack_names, region):
    cfn = s.client('cloudformation', region_name=region)
    account_id = get_account_id(s)
    account_name = get_account_name(s)
    global resources
    for stack_name in stack_names:
        res = cfn.describe_stack_resource_drifts(StackName=stack_name)
        print(f'Processing resource drift for {stack_name} {region}')
        for resource in res['StackResourceDrifts']:
            _resource = {}
            _resource['AccountName'] = account_name
            _resource['AccountId'] = account_id
            _resource['Region'] = region
            _resource['StackName'] = stack_name
            _resource['LogicalResourceId'] = resource['LogicalResourceId']
            _resource['PhysicalResourceId'] = resource['PhysicalResourceId']
            _resource['ResourceType'] = resource['ResourceType']
            _resource['StackResourceDriftStatus'] = resource['StackResourceDriftStatus']
            _resource['Timestamp'] = resource['Timestamp'].replace(tzinfo=None)
            try: 
                if resource['StackResourceDriftStatus'] in ['IN_SYNC', 'DELETED']:
                    resources.append(_resource)
                else:
                    for property_diff in resource['PropertyDifferences']:
                        _resource['DifferenceType'] = property_diff['DifferenceType']
                        _resource['PropertyPath'] = property_diff['PropertyPath']
                        _resource['ExpectedValue'] = property_diff['ExpectedValue']
                        _resource['ActualValue'] = property_diff['ActualValue']
                        resources.append(_resource)
            except KeyError as e:
                print(resource['PhysicalResourceId'])
                print(f'KeyError {e} \n{_resource}') 

    


