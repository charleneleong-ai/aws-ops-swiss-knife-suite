#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 12:53:50 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, August 11th 2020, 3:15:21 am
###

import os
import sys
import argparse
import logging
import boto3
import pandas as pd

from src.cfn.cfn_drift import handler as cfn_drift_handler
from src.inventory.ssm_inventory import handler as ssm_inventory_handler
from src.inventory.ec2_inventory import handler as ec2_inventory_handler
from src.inventory.compare_ssm_ec2_inventory import handler as compare_ssm_ec2_inventory_handler
from src.ec2.delete_default_vpcs import handler as delete_default_vpcs_handler
from src._lambda.clean_lambda_versions import handler as clean_lambda_versions_handler
from src.utils import get_profiles

# logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')


def main(args):
    # ========= Loading profiles ========= #
    if args.customer:
        profiles = get_profiles(args.customer)
        print(f'Loading accounts for the customer [ {args.customer} ] from AWS config')
    else:
        if os.getenv('AWSUME_PROFILE'):
            account_name = os.getenv('AWSUME_PROFILE')
            profiles = [account_name]
        else:
            print('\nPlease assume a role via awsume.\nawsume <PROFILE_NAME> -a\n')
            sys.exit(1)
            
    if args.exclude:
        for ex_profile in args.exclude:
            profiles.remove(ex_profile)

    print(profiles)
    
    # ========= Building dataframe ========= #
    customer_df = pd.DataFrame()
    for profile in profiles:
        print(f'\n\n# ========= Preparing report for {profile} ========= #')

        if args.method == 'cfn-drift':
            df = cfn_drift_handler(profile, args.region)
        elif args.method == 'ssm-inventory':
            df = ssm_inventory_handler(profile, args.region)
        elif args.method == 'ec2-inventory':
            df = ec2_inventory_handler(profile, args.region)
        elif args.method == 'compare-ssm-ec2-inventory':
            df = compare_ssm_ec2_inventory_handler(profile, args.region)
        # elif args.method == 'delete-default-vpcs':
        #     df = delete_default_vpcs_handler(profile, args.region)
        elif args.method == 'clean-lambda-versions':
            df = clean_lambda_versions_handler(profile, args.region, args.mode, args.output)
        
        if args.output:
            customer_df = pd.concat([customer_df, df])

    # ========= Outputing the results to a report ========= #
    if args.output:
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        if args.customer:
            account_name = args.customer
        output_report(df=customer_df,
                        account_name=account_name, 
                        report_name=args.method, 
                        ext=args.output, 
                        sheet_name=args.method.replace('-', '').capitalize())
            


def output_report(df, account_name, report_name, ext, sheet_name):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    OUTPUT_PATH = os.path.join(OUTPUT_FOLDER, f'{account_name}-{report_name}.{ext}')
    if ext == 'xlsx':
        df.to_excel(OUTPUT_PATH, sheet_name=sheet_name)
    elif ext == 'csv':
        df.to_csv(OUTPUT_PATH)
    else:
        raise ValueError('Invalid File Extension')
    print(f'\n\n# ========= Saved {account_name}-{report_name}.{ext} report ========= #')
    print(f'{OUTPUT_PATH}')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save CFN Drift Detection report to file')
    parser.add_argument('-c', '--customer', metavar='customer', default='', help='Customer to filter') 
    parser.add_argument('-e', '--exclude', metavar='account-name',  nargs='+', default='', help='Exclude certain accounts') 
    parser.add_argument('-o', '--output', default=None, choices=['xlsx', 'csv', None], help='Output File Format - xlsx [default] or csv')
    parser.add_argument('-mt', '--method', 
                        choices=['cfn-drift', 'ssm-inventory', 'ec2-inventory', 'compare-ssm-ec2-inventory', 'delete-default-vpcs', 'clean-lambda-versions'], 
                        help='Method of operation')
    parser.add_argument('-m', '--mode', metavar='scan', choices=['scan', 'run'], default='scan', help='Checks whether to perform a scan or run')
    parser.add_argument('-r', '--region', help='If unspecified, runs across all regions.')
    args = parser.parse_args()
    main(args)
