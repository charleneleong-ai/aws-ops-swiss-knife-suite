#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Thursday, June 11th 2020, 2:56:57 pm
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Tuesday, July 21st 2020, 2:01:58 pm
###

import boto3



def get_stack_names(region, session=None):
    cfn = boto3.client('cloudformation', region_name=region)
    if session: session.client('cloudformation', region_name=region)
    paginator = cfn.get_paginator('list_stacks')
    response_iterator = paginator.paginate(
        StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']
    )
    stack_names = []
    for res in response_iterator:
        for stack in res['StackSummaries']:
            stack_names.append(stack['StackName'])
    return stack_names


    
def stack_exists(stack_name, session=None):
    cfn = boto3.client('cloudformation')
    paginator = cfn.get_paginator('list_stacks')
    for page in paginator.paginate():
        for stack in page['StackSummaries']:
            if stack['StackStatus'] == 'DELETE_COMPLETE':
                continue
            if stack['StackName'] == stack_name:
                return True
    return False



def parse_template_file(template, session=None):
    cfn = boto3.client('cloudformation')
    if session: cfn = session.client('cloudformation')
    with open(template) as template_fileobj:
        template_data = template_fileobj.read()
    cfn.validate_template(TemplateBody=template_data)
    return template_data



def parse_params_file(parameters, session=None):
    cfn = boto3.client('cloudformation')
    if session: cfn = session.client('cloudformation')
    with open(parameters) as parameter_fileobj:
        parameter_data = json.load(parameter_fileobj)
    return parameter_data



def cfn_delete(stack_name, session=None):
    cfn = boto3.client('cloudformation')
    if session: cfn = session.client('cloudformation')
    cfn.delete_stack(StackName=stack_name)
    print(f'\nCleaning up resources for {stack_name}...')

