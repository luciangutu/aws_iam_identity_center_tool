# aws_iam_identity_center_tool
Collection of Python scripts to manage the AWS IAM Identity Center (SSO)

Generates a JSON output:
```JSON
{
    "123456789012": {
        "alias": "Production",
        "users": {
            "jdoe@example.com": [
                "AdministratorAccess"
            ],
            "user1@example.com": [
                "PowerUserAccess"
            ]
        }
    },
    "012345678901": {
        "alias": "Dev",
        "users": {
            "jdoe@example.com": [
                "AdministratorAccess"
            ]
        }
    }
}
```
