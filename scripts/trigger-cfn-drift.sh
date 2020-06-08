#!/usr/bin/env bash


for stack in $(aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE ROLLBACK_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE --query 'StackSummaries[].StackName' --output text); do 
    aws cloudformation detect-stack-drift --stack-name "$stack"; 
done