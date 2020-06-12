#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Tuesday, June 9th 2020, 2:49:45 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Friday, June 12th 2020, 9:15:50 am
###

import os
import argparse
import logging
import boto3
import pandas as pd

from src.cfn.create_changeset import handler as create_changeset_handler
from src.cfn.create_update_stack import handler as create_update_stack_handler
from src.utils import get_profiles

# logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')


def main(args):
    # ========= Loading profiles ========= #
    if args.customer:
        profiles = get_profiles(args.customer)
        print(f'Loading accounts for the customer [ {args.customer} ] from AWS config')
    else:
        account_name = boto3.client('iam').list_account_aliases()['AccountAliases'][0]
        profiles = [account_name]

    if args.exclude:
        for ex_profile in args.exclude:
            profiles.remove(ex_profile)
    
    print(profiles)

    # ========= Building dataframe ========= #
    customer_df = pd.DataFrame()
    for profile in profiles:
        print(f'\n\n# ========= Preparing report for {profile} ========= #')
        if args.method == 'create-changeset':
            df = create_changeset_handler(profile, args.region)
        if args.method == 'create-stack':
            df = create_update_stack_handler(profile, args.region)

    # ========= Outputing the results to a report ========= #
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    if args.customer:
        account_name = args.customer
        
    output_report(df=df, 
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
    parser.add_argument('-o', '--output', default='xlsx',  metavar='xlsx', choices=['xlsx', 'csv'], help='Output File Format - xlsx [default] or csv')
    parser.add_argument('-m', '--method', choices=['create-changeset', 'create-stack', 'update-stack'], help='Method of operation')
    parser.add_argument('-r', '--region', help='If unspecified, runs across all regions.')
    args = parser.parse_args()
    main(args)
