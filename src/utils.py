#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Thursday, May 14th 2020, 2:58:25 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Thursday, June 11th 2020, 3:46:21 pm
###

import boto3
from re import match, sub

from os.path import expanduser
import configparser
import pytz


nzst = pytz.timezone('Pacific/Auckland')


def utc_to_nzst(utc_dt):
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(nzst)


def get_regions(service, session=None):
    regions = boto3.session.Session().get_available_regions(service)
    if session: regions = session.get_available_regions(service)
    regions.remove('ap-east-1')  # Not available to call
    regions.remove('me-south-1')
    regions.remove('af-south-1')
    regions.remove('eu-south-1')
    return regions


def get_profiles(customer):
    home = expanduser('~')
    config = configparser.RawConfigParser()
    config_path = config.read(f'{home}/.aws/config')
    profiles = config.sections()
    profiles = [profile.replace('profile ', '')
                for profile in profiles if customer in profile]
    return profiles


def without(d, key):
    new_d = d.copy()
    new_d.pop(key)
    return new_d


def role_exists(role_name, session=None):
    iam = boto3.client('iam')
    if session: iam = session.client('iam')
    try:
        iam.get_role(RoleName=role_name)
        result = True
    except Exception:
        result = False
    return result


def get_account_name(session=None):
    iam = boto3.client('iam')
    if session: iam = session.client('iam')
    return iam.list_account_aliases()['AccountAliases'][0]



def get_account_id(session=None):
    sts = boto3.client('sts')
    if session: sts = session.client('sts')
    return sts.get_caller_identity()['Account']



def list_children(ou_id, child_type, session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    children = []
    paginator = org.get_paginator('list_children')
    for page in paginator.paginate(ParentId=ou_id, ChildType=child_type):
        children += page['Children']
    return children



def list_org_roots(session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    value = None
    try:
        root_info = org.list_roots()
    except Exception as exe:
        raise ValueError(f'Script should run on Organization root only: {str(exe)}')
    if 'Roots' in root_info:
        value = root_info['Roots'][0]['Id']
    else:
        raise ValueError(f'Unable to find valid root: {str(root_info)}')
    return value



def list_all_ou(session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    org_info = list()
    root_id = list_org_roots()
    
    children = list_children(root_id, child_type='ORGANIZATIONAL_UNIT')
    for item in children:
        org_info.append(item['Id'])
    if len(org_info) == 0:
        raise ValueError('No Organizational Units Found')
    return org_info



def get_ou_map(session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    ou_list = list_all_ou()
    ou_map = {}
    for ou_item in ou_list:
        try:
            ou_describe = org.describe_organizational_unit(OrganizationalUnitId=ou_item)
            ou_info = ou_describe['OrganizationalUnit']
            ou_map[ou_info['Name']] = ou_info['Id']
        except Exception as exe:
            raise ValueError(f'Unable to get the OU information {str(exe)}')
    return ou_map



def get_ou_details(ou_name=None, ou_id=None):
    output = None
    ou_map = get_ou_map()
    if ou_name:
        if ou_name in ou_map:
            output = ou_map[ou_name]
        else:
            raise ValueError(f'Unable to find {ou_name}: {str(ou_map)}')
    elif ou_id:
        if ou_id in ou_map.values():
            for ou_item in ou_map:
                if ou_map[ou_item] == ou_id:
                    output = ou_item
        else:
            raise ValueError(f'Unable to find {ou_name}: {str(ou_map)}')
    else:
        raise ValueError('Invalid Input recieved')
    return output



def get_ou_id(ou_info):
    ou_id = None
    ou_id_matched = bool(match('^ou-[0-9a-z]{4,32}-[a-z0-9]{8,32}$', ou_info))
    if ou_id_matched:
        ou_id = ou_info
    else:
        ou_id = get_ou_details( ou_name=ou_info)
    return ou_id



def list_of_accounts_in_ou(ou_id, session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    result = []
    account_map = {}
    try:
        result = org.list_accounts_for_parent(ParentId=ou_id)['Accounts']
        org_page_iterator = org.get_paginator('list_accounts_for_parent').paginate(ParentId=ou_id)
    except Exception as exe:
        raise ValueError(f'Unable to get Accounts list: {str(exe)}')
    for page in org_page_iterator:
        result += page['Accounts']
    for item in result:
        account_map[item['Id']] = {'Email': item['Email'], 'Name': item['Name']}
    return account_map



def is_master(session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    master_account_id = org.describe_organization()['Organization']['MasterAccountId']
    return(master_account_id == get_account_id())



def ou_exists(ou_name, session=None):
    org = boto3.client('organizations')
    if session: org = session.client('organizations')
    ous = org.list_organizational_units_for_parent(ParentId=list_org_roots())['OrganizationalUnits']
    for ou in ous:
        if ou['Name'] == ou_name:
            return True
    return False


