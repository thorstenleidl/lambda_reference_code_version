from __future__ import print_function
import json
import boto3
import os
import zipfile
import tempfile

def lambda_handler(event, context):
    """Lambda Function for writing Source Version and Commit Message in Description of Beanstalk Application Version."""

    print("Start")

    # Print event for debugging
    print("Event: {}".format(event))

    # Debug Setup
    DEBUG = os.environ.get('DEBUG', None)
    if DEBUG:
        debug_session = boto3.Session(profile_name='servicedesk')
        eb_client = debug_session.client('elasticbeanstalk')
        cp_client = debug_session.client('codepipeline')
        s3_resource = debug_session.resource('s3')
    else:
        eb_client = boto3.client('elasticbeanstalk')
        cp_client = boto3.client('codepipeline')
        s3_resource = boto3.resource('s3')

    # Get job id for response to CodePipeline
    job_id = event['CodePipeline.job']['id']

    try:
        # Get variables from event input
        commit_message = event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters']
        s3_bucket_name = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['bucketName']
        s3_object_key = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['objectKey']
    except Exception as e:
        print("Error event")
        cp_client.put_job_failure_result(jobId=job_id, failureDetails={'message': ('Function exception: ' + str(e)), 'type': 'JobFailed'})
        return 

    try:
        # Read out data from package.json on s3 zip object
        with tempfile.TemporaryFile() as f:
            s3_resource.meta.client.download_fileobj(s3_bucket_name, s3_object_key, f)
            archive = zipfile.ZipFile(f)
            package_json = archive.open('package.json')
            data = package_json.read() 
            json_data = json.loads(data)
            application_version = json_data['version']
            application_name = "{}-terraform".format(json_data['name'])
            pipeline_name = "{}-pipeline".format(json_data['name'])
    except Exception as e:
        print("Error s3")
        cp_client.put_job_failure_result(jobId=job_id, failureDetails={'message': ('Function exception: ' + str(e)), 'type': 'JobFailed'})
        return    

    try:
        # Read out newest version-label from environemt 
        environment = eb_client.describe_environments(ApplicationName=application_name)
        version_label = environment['Environments'][0]['VersionLabel']
        
        # Build description string
        description = 'Version: {} - Commit Message: {}'.format(application_version, commit_message)

        # Write new Description to given elastic Beanstalk Application version 
        eb_response = eb_client.update_application_version(
        ApplicationName=application_name,
        VersionLabel=version_label,
        Description=description
        )
    except Exception as e:
        print("Error Eb")
        cp_client.put_job_failure_result(jobId=job_id, failureDetails={'message': ('Function exception: ' + str(e)), 'type': 'JobFailed'})
        return

    # Put Info to Code Pipeline, if Code succeeded
    cp_client.put_job_success_result(jobId=job_id)

    print("Ende")
    return

# Local Debugging
if __name__ == "__main__":

    f = open("{}/test/event.json".format(os.path.dirname(__file__), "r"))
    event = json.load(f)
    f.close()

    lambda_handler(event, None)