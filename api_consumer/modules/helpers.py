import os, json, boto3
from os.path import join
 
def create_folder_structure(folder_name, currency, asset, messages):

    try:
        for message in messages:
            os.makedirs(join('data', folder_name, currency, asset, message))

        print('\n*Creating folder ', folder_name)
        print('\n*Creating folder ', join(folder_name, currency))

    except FileExistsError as err:
        print('Existing folder!', err)
        return False
    
    return True
    
def write_file(fullpath, content = False):
        file_object = open(fullpath, 'a')

        if content:
            file_object.write('[' if os.path.getsize(fullpath) is 0 else ',') # includes data as if it was inside a list
            file_object.write(json.dumps(content))
        else:
            file_object.write(']') # closes the list once there is no more content, i.e. the application is closed
        
        file_object.close()

def upload_to_aws(local_path, bucket, s3_path, access_key, secret_key):
    try:
        s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        s3.upload_file(local_path, bucket, s3_path)
        print("Upload Successful: ", s3_path)
        return True
        
    except Exception as e:
        print(e)
