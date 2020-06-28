# Ops Swiss Knife Suite

Small toolbox for generating small reports.

Currently supports the following features - 

  1. Detect all Cloudformation drift
  2. Report on SSM inventory
  3. Report on EC2 inventory 
  4. Compares SSM and EC2 inventory to see what instances need to be configured

This can run over all regions and all customer accounts.

## Requirements 
- [Python 3.7.5](https://docs.python-guide.org/starting/install3/osx/)
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
  - [Awsume](https://awsu.me/general/quickstart.html) (ability to assume role)


### Create virtualenv
    $ python -m venv .venv
    $ source .venv/bin/activate


### Install dependencies

    $ pip install -r requirements-dev.txt


### Run app
Default output is Excel but can also output CSV.

The script assumes profiles using your AWS config file in `~/.aws/config`, please make sure this is configured correctly and you have permissions to assume into the profiles. Specifying a customer will filter profiles for only accounts that contain the customer name.

There is an option also to exclude certain accounts.

Arguments:

  * **c, customer [optional]**: Customer to filter. If not defined, will perform script on currently assumed role.
  * **o, output**: Specifies output file format, CSV or Excel. **Default** is Excel (xlsx)
  * **e, exclude**: Excludes specified accounts read in from your `~/.aws/config` file.
  * **m, method**: Can support Cloudformation drift, SSM inventory, EC2 inventory and SSM and EC2 inventory comparison
    * ['cfn-drift', 'ssm-inventory', 'ec2-inventory', 'compare-ssm-ec2-inventory', 'delete-default-vpcs']
  * **r, region**: If unspecified, runs across all regions.

Try it out! Please report any bugs! 

Example command - 

```bash
$ python report.py --output csv --customer chorus --method compare-ssm-ec2-inventory --region ap-southeast-2
$ python report.py --output xlsx --customer contact --method cfn-drift --region ap-southeast-2
```


Output is saved to `output` folder with file name `{account_name}-{method}.{ext}`.