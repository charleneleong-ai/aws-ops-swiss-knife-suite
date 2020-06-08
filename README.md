# Reporting Cloudformation Drift in AWS Account

Triggers Drift Detection on all Cloudformation stacks and outputs resource drift status and differences to Excel or CSV file.


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

Try it out! Please report any bugs! 

Example command - 

```bash
$ python app.py --output xlsx --customer contact --exclude contact-identity
```

### To output scan to a file
Output can be saved as CSV or XLSX file depending on the specified extension (xlsx or csv).

```bash
$ python app.py --output xlsx --customer contact --exclude contact-identity
```

Output is saved to `output` folder with file name `{account_name}-cfn-drift-report.{ext}`.