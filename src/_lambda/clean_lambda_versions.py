#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Tuesday, July 21st 2020, 2:02:21 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, July 21st 2020, 4:19:47 pm
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



def handler(profile, region, dryrun, output_mode):
    global s
    s = awsume(profile)
    global run
    run = dryrun
    global output
    output = output_mode

    regions = [region] if region else get_regions('lambda')
    for region in regions:
        clean_lambda_versions(region)
    
    return pd.DataFrame(resources)



def clean_lambda_versions(region):
    client = s.client('lambda')
    functions = client.list_functions()['Functions']
    account_id = get_account_id(s)
    account_name = get_account_name(s)
    for function in functions:
        versions = client.list_versions_by_function(FunctionName=function['FunctionArn'])['Versions']

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
        
        version_range = (len(versions)-5) if ((len(versions)-5) >=0) else 5
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
