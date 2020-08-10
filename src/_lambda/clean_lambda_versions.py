#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Tuesday, July 21st 2020, 2:02:21 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, August 11th 2020, 3:52:00 am
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
run = False
output = False



def handler(profile, region, run_mode, output_mode):
    global s
    s = awsume(profile)
    if run_mode=='run':
        global run
        run = True
    global output
    output = output_mode

    regions = [region] if region else get_regions('lambda')
    with ThreadPool(processes=10) as pool:
        t = pool.map(clean_lambda_versions, regions)
    
    return pd.DataFrame(resources)



def clean_lambda_versions(region):
    if output: global resources
    client = s.client('lambda')
    functions = client.list_functions()['Functions']
    account_id = get_account_id(s)
    account_name = get_account_name(s)
    print(f'\nCleaning Lambda versions in {region}\n===================')

    for function in functions:
        print(f"{function['FunctionArn']}\n")
        versions = list_versions_by_function(function['FunctionArn'])
        version_range = (int(versions[-1]['Version'])-5) if ((len(versions)-5) >=0) else 5

        for version in versions:
            try:
                version_num = int(version['Version'])   # Skip aliases and $LATEST
            except:
                continue
            if version_num <= version_range:
                arn = version['FunctionArn']
                print(f'delete_function(FunctionName={arn})')
                if run: 
                    client.delete_function(FunctionName=arn)

        if output:
            _resource = {}
            _resource['AccountName'] = account_name
            _resource['AccountId'] = account_id
            _resource['Region'] = region
            _resource['FunctionName'] = function['FunctionName']
            _resource['Runtime'] = function['Runtime']
            _resource['LastModified'] = function['LastModified']
            _resource['NumVersions'] = len(versions)
            resources.append(_resource)



def list_versions_by_function(function_name):
    client = s.client('lambda')
    versions = []
    paginator = client.get_paginator('list_versions_by_function')
    for page in paginator.paginate(FunctionName=function_name):
        versions += page['Versions']
    return versions
