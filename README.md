# AWS Lambda function to reference the application versions to CodePipeline

This function has to be triggerd by CodePipeline and updates the description of an Elastic Beanstalk application version.

## Prerequisities

### Boto3 authentication

You have to provide valid credentials in your "~/.aws/credentials" file

### Naming

The name from package.json has to be the same name as your Elastic Beanstalk application without "-terraform" (e.g. name in package.json = "example", Elastic Beanstalk application is named "example-terraform"), otherwise you can edit the code in line 50.
The name of the CodePipeline has to be in the same structure (e.g. name in package.json = "example", CodePipeline is named "example-pipeline"), otherwise you can edit the code in line 51.

### CodePipeline stage structure

* Source
* Build (necessary to set output artifact with a custom name for e.g. build_output)
* Approval (optional)
* Deploy
* Lambda (explained below)

### CodePipeline Lambda stage configuration

* User Parameter: #{source_variables.CommitMessage}
* Input artifacts: build_output (name has to be the same as the output artifact name in the build stage)
