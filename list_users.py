#!/usr/bin/env python3
# list users from all AWS Accounts in AWS IAM Identity Center (successor to AWS Single Sign-On/AWS SSO)
import boto3
import itertools
import json
import time
from botocore.config import Config
from botocore.exceptions import ClientError

config = Config(
   retries={
      'max_attempts': 10,
      'mode': 'adaptive'
   }
)

region = 'us-west-2'

def do_stuff(_acc, _perm):
    retries = 100
    retry = True
    while retry:
        try:
            res = client_sso.describe_permission_set(
                InstanceArn=sso_instance_arn,
                PermissionSetArn=_perm
            )
        except ClientError as e:
            # print(e)
            if e.response['Error']['Code'] == 'ThrottlingException':
                retries += 1
                time.sleep((2 ^ retries*100)/1000)
        else:
            retry = False

    permissions_set_name = res["PermissionSet"]["Name"]
    print(f'Looking in {_acc} account and {permissions_set_name} permission set...')
    retry = True
    while retry:
        try:
            r1 = client_sso.list_account_assignments(
                InstanceArn=sso_instance_arn,
                AccountId=_acc,
                PermissionSetArn=_perm
            )
        except ClientError as e:
            # print(e)
            if e.response['Error']['Code'] == 'ThrottlingException':
                retries += 1
                time.sleep((2 ^ retries*100)/1000)
        else:
            retry = False

    for acc_assignments in r1["AccountAssignments"]:
        if acc_assignments:
            retry = True
            while retry:
                try:
                    r2 = client_ids.describe_user(
                        IdentityStoreId=sso_instance_id,
                        UserId=acc_assignments["PrincipalId"]
                    )
                    username = r2['UserName']
                    # update the records with username and permission
                    if username not in final_dict[_acc]['users']:
                        final_dict[_acc]['users'][username] = []
                    final_dict[_acc]['users'][username].append(permissions_set_name)
                except ClientError as e:
                    # print(e)
                    if e.response['Error']['Code'] == 'ThrottlingException':
                        retries += 1
                        time.sleep((2 ^ retries * 100) / 1000)
                else:
                    retry = False


# final dict with AWS accounts and users in each account
final_dict = {}
accounts_set = set()
permissions_set = set()

client_sso = boto3.client('sso-admin', region_name=region, config=config)
client_ids = boto3.client('identitystore', region_name=region, config=config)
client_org = boto3.client('organizations', region_name=region, config=config)

# get the IdentityStoreId
response = client_sso.list_instances()
sso_instance_id = response["Instances"][0]["IdentityStoreId"]
sso_instance_arn = response["Instances"][0]["InstanceArn"]

# build the permissions sets set
response = client_sso.list_permission_sets(
    InstanceArn=sso_instance_arn
)
permissions_set.update(response["PermissionSets"])

while "NextToken" in response:
    response = client_sso.list_permission_sets(
        InstanceArn=sso_instance_arn,
        NextToken=response["NextToken"]
    )
    permissions_set.update(response["PermissionSets"])

# build the account IDs set based on permissions sets
for permission_set in permissions_set:
    r = client_sso.list_accounts_for_provisioned_permission_set(
        InstanceArn=sso_instance_arn,
        PermissionSetArn=permission_set
    )
    accounts_set.update(r["AccountIds"])

for acc in accounts_set:
    # initiate the key for AWS account with an empty dict
    # then add the key for alias and users
    final_dict[acc] = {}
    try:
        final_dict[acc].update({'alias': client_org.describe_account(AccountId=acc).get('Account').get('Name')})
    except Exception as err:
        print(f"Err: {err}")
    final_dict[acc]['users'] = {}

all_combinations_acc_perm = list(itertools.product(accounts_set, permissions_set))
print(f'Found {len(permissions_set)} Permission Sets and {len(accounts_set)} accounts for {sso_instance_id}')

for acc, perm in all_combinations_acc_perm:
    do_stuff(acc, perm)

print(json.dumps(final_dict, indent=4, sort_keys=True, default=str))
