#!/usr/bin/env bash

aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE ROLLBACK_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE --query 'sort_by(StackSummaries, &StackName)[*].[StackName, StackStatus, DriftInformation.StackDriftStatus, DriftInformation.LastCheckTimestamp]' --output table