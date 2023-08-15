import configparser
import os
import sys
import re

import boto3

# Monark Basak
# 1056289
# mbasak@uoguelph.ca


class S5:
    def __init__(self) -> None:
        self.s3 = None
        self.cloud_bucket: str = ""  # used for chlocn
        self.cloud_path: str = ""  # used for chlocn

    def start(self):
        self.read_config_file()
        print("Welcome to the AWS S3 Storage Shell (S5)")

        try:
            self.s3 = boto3.Session(aws_access_key_id=self.aws_access_key_id,
                                    aws_secret_access_key=self.aws_secret_access_key)

            # if valid
            print("You are now connected to your S3 storage.")
        except Exception as e:
            # invalid
            print("You could not be connected to your S3 storage.")
            print("Please review procedures for authenticating your account on AWS S3.")
            sys.exit(1)

        user_input = ""

        while user_input != "quit" and user_input != "exit":
            user_input = input("S5> ")
            tokenized_input = user_input.split()

            try:
                # local to cloud copy
                if tokenized_input[0].lower() not in ["locs3cp", "s3loccp", "create_bucket", "create_folder", "chlocn", "cwlocn", "list", "s3copy", "s3delete", "delete_bucket", "exit", "quit", "cd", "ls", "pwd"]:
                    print(
                        """
Only valid functions are:
    - locs3cp
    - s3loccp
    - create_bucket
    - delete_bucket
    - create_folder
    - chlocn
    - cwlocn
    - list
    - s3copy
    - s3delete
    - cd
    - ls
    - pwd
""")
                elif len(tokenized_input) != 3 and tokenized_input[0] in ["locs3cp", "s3loccp", "s3copy"]:
                    print("Incorrect number of arguments provided.")
                elif tokenized_input[0].lower() == "locs3cp":
                    self.locs3cp(
                        tokenized_input[1], tokenized_input[2])
                elif tokenized_input[0].lower() == "s3loccp":
                    self.s3loccp(
                        tokenized_input[1], tokenized_input[2])
                elif len(tokenized_input) != 2 and tokenized_input[0] in ["delete_bucket", "create_bucket", "create_folder", "chlocn", "s3delete"]:
                    print("Incorrect number of arguments provided.")
                elif tokenized_input[0].lower() == "create_bucket":
                    self.create_bucket(tokenized_input[1])
                elif tokenized_input[0].lower() == "delete_bucket":
                    self.delete_bucket(tokenized_input[1])
                elif tokenized_input[0].lower() == "create_folder":
                    self.create_folder(tokenized_input[1])
                elif tokenized_input[0].lower() == "chlocn":
                    self.change_cloud_location(tokenized_input[1])
                elif tokenized_input[0].lower() == "cwlocn":
                    self.print_current_cloud_directory()
                elif tokenized_input[0].lower() == "s3copy":
                    self.s3_copy(
                        tokenized_input[1], tokenized_input[2])
                elif tokenized_input[0].lower() == "s3delete":
                    self.s3_delete(tokenized_input[1])
                elif len(tokenized_input) > 3 and tokenized_input[0] == "list":
                    print("Incorrect number of arguments provided.")
                elif tokenized_input[0].lower() == "list":
                    if "-l" in tokenized_input:
                        self.list_cloud_directory(
                            "" if len(tokenized_input) == 2 else tokenized_input[2], True)
                    elif len(tokenized_input) == 1:
                        self.list_cloud_directory("", False)
                    else:
                        self.list_cloud_directory(
                            tokenized_input[1] or "", False)
                elif tokenized_input[0].lower() == "cd":
                    self.change_dir_local(tokenized_input[1])
                elif tokenized_input[0].lower() == "ls":
                    self.list_directory_local()
                elif tokenized_input[0].lower() == "pwd":
                    self.current_working_dir_local()

            except IndexError as error:
                # didn't give local path and/or cloud path
                print("Not enough arguments provided.")

        return 0

    def read_config_file(self):
        # find config file
        config_file = [file for file in os.listdir(
            '.') if file.lower() == "s5-s3.conf"]

        if len(config_file) == 0:
            print("Config file is missing!")
            sys.exit(1)

        # grab aws key id and access key
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file)

        self.aws_access_key_id = config_parser['default']['aws_access_key_id']
        self.aws_secret_access_key = config_parser['default']['aws_secret_access_key']

    def get_buckets(self):
        buckets = self.s3.client('s3').list_buckets()

        return buckets

    def get_bucket_names(self):
        """
        returns a list of names of buckets that exist in s3
        """
        buckets = self.get_buckets()
        bucket_names = []

        for bucket in buckets['Buckets']:
            bucket_names.append(bucket['Name'])

        return bucket_names

    def check_bucket_exists(self, cloud_path: str):
        # check the correct format is passed
        if cloud_path.startswith('/') != True:
            return False

        tokenized_cloud_path = cloud_path.split('/')

        # cloud path doesn't contain bucket
        if len(tokenized_cloud_path) < 2:
            return False

        # check there's a bucket name
        bucket_name = tokenized_cloud_path[1]
        s3_res = self.s3.resource('s3')

        if s3_res.Bucket(bucket_name) not in s3_res.buckets.all():
            return False

        return True

    def objects_in_bucket(self, cloud_path: str):
        tokenized_cloud_path = cloud_path.split('/')

        # get bucket
        bucket_name = tokenized_cloud_path[1]

        # check path exists
        s3_client = self.s3.client('s3')

        bucket_objs = s3_client.list_objects_v2(Bucket=bucket_name)

        return [item["Key"] for item in bucket_objs['Contents']] if bucket_objs['KeyCount'] > 0 else []

    def directory_exists_in_cloud(self, cloud_path: str, dst_flag=None):
        tokenized_cloud_path = cloud_path.split('/')

        # get bucket
        bucket_name = tokenized_cloud_path[1]

        # check path exists
        s3_client = self.s3.client('s3')

        cloud_dirs: list = [item["Key"] for item in s3_client.list_objects_v2(
            Bucket=bucket_name)['Contents']]

        exists: bool = False
        for cloud_item in cloud_dirs:
            tokenized_cloud_item = cloud_item.split('/')

            if tokenized_cloud_item[:-1] == tokenized_cloud_path[2:] and tokenized_cloud_item[-1] == "" and dst_flag == True:
                exists = True
            elif tokenized_cloud_item[0:] == tokenized_cloud_path[2:]:
                exists = True

        return exists

    def generate_valid_cloud_path(self, cloud_path: str, dst_flag=None):
        # return a string that represents a valid cloud path depending on whether an absolute or relative path was sent in
        tokenized_cloud_path: list = cloud_path.split('/')

        # file will not exist so check will always unless the file name is removed
        if dst_flag == True:
            tokenized_cloud_path.pop()

        if len(self.cloud_bucket) == 0 and len(self.cloud_path) == 0 and len(tokenized_cloud_path) <= 1:
            return "/"
        elif len(self.cloud_bucket) == 0 and self.check_bucket_exists(cloud_path) == False:
            return "/"
        elif self.check_bucket_exists(cloud_path):
            return cloud_path
        elif self.check_bucket_exists(cloud_path) == False and len(self.cloud_bucket) != 0 and cloud_path.startswith('/') == False:
            # cloud bucket valid in instance and using relative path
            if self.directory_exists_in_cloud(f"/{self.cloud_bucket}/{'/'.join(tokenized_cloud_path)}", dst_flag) and len(self.cloud_path) == 0:
                # valid relative path
                return f"/{self.cloud_bucket}/{cloud_path.strip('/')}"
            elif self.directory_exists_in_cloud(f"/{self.cloud_bucket}/{self.cloud_path.rstrip('/')}/{'/'.join(tokenized_cloud_path)}", dst_flag):
                return f"/{self.cloud_bucket}/{self.cloud_path.rstrip('/')}/{cloud_path}"
            else:
                # invalid relative path
                return f"/{self.cloud_bucket}" if len(self.cloud_path) == 0 else f"/{self.cloud_bucket}/{self.cloud_path}"
        elif len(self.cloud_bucket) > 0:
            return f"/{self.cloud_bucket}" if len(self.cloud_path) == 0 else f"/{self.cloud_bucket}/{self.cloud_path}"

        return "/"

    def create_bucket(self, bucket_name):
        try:
            if bucket_name.startswith('/') == False:
                print("Bucket name MUST start with a '/'. Example: /new_bucket")
                return 1

            bucket_name = bucket_name.strip('/')
            bucket_names = self.get_bucket_names()

            if bucket_name in bucket_names:
                print("This bucket name already exists!")
                return 1

            # create new bucket
            s3_client = self.s3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name.strip('/'), CreateBucketConfiguration={
                                    'LocationConstraint': 'ca-central-1'})

            # display the new bucket changes in s3
            bucket_names = self.get_bucket_names()
            print(f"Bucket {bucket_name} successfully created.")
            print("List of current buckets:")
            for bucket in bucket_names:
                print(bucket)

        except Exception as e:
            print("Cannot create bucket.")

            return 1

        return 0

    def delete_bucket(self, bucket_name: str):
        try:
            if bucket_name.startswith('/') == False:
                print("Bucket name MUST start with a '/'. Example: /delete_bucket")
                return 1

            bucket_name = bucket_name.strip('/')
            bucket_names = self.get_bucket_names()

            if bucket_name not in bucket_names:
                print("This bucket doesn't exist!")
                return 1

            # make sure bucket doesn't have objects
            s3_client = self.s3.client('s3')
            bucket_object_count = s3_client.list_objects_v2(Bucket=bucket_name)[
                'KeyCount']

            if bucket_object_count != 0:
                print("Cannot delete bucket with objects!")
                return 1

            # prevent user from deleting bucket they are in
            if self.cloud_bucket == bucket_name:
                print("Cannot delete bucket you are currently in!")

                return 1

            # delete bucket specified
            s3_client.delete_bucket(Bucket=bucket_name.strip('/'))

            # display the new bucket changes in s3
            bucket_names = self.get_bucket_names()
            print(f"Bucket {bucket_name} successfully deleted.")
            print("List of current buckets:")
            for bucket in bucket_names:
                print(bucket)
        except Exception as e:
            print("Cannot delete bucket.")

            return 1

        return 0

    def locs3cp(self, local_path: str, cloud_path: str):
        try:
            # check local path
            local_file = ""
            if local_path.startswith("/") == True and os.path.exists(local_path) and os.path.isfile(local_path):
                # absolute path
                local_file = local_path
            elif local_path.startswith("/") == False and os.path.exists(local_path) and os.path.isfile(local_path):
                # relative path
                local_file = os.path.abspath(local_path)
            else:
                print("Local path provided doesn't exist or isn't a file.")
                return 1

            # check the cloud path
            tokenized_cloud_path = self.current_cloud_directory(
                cloud_path).split('/')
            bucket_name = tokenized_cloud_path[1] if len(
                tokenized_cloud_path) > 1 else "/"

            # check bucket exists
            if self.check_bucket_exists('/'.join(tokenized_cloud_path)) == False:
                print("Bucket provided doesn't exist.")
                return 1

            s3_client = self.s3.client('s3')

            # create object path
            object_path = '/'.join(tokenized_cloud_path[2:])

            try:
                # check file doesn't already exist in cloud
                key_count = s3_client.list_objects_v2(
                    Bucket=bucket_name, Prefix=object_path)['KeyCount']
                if key_count != 0:
                    print("This file already exists!")
                    return 1

                # upload file to S3 bucket
                s3_client.upload_file(local_file, bucket_name, object_path)
            except Exception as e:
                print("Failed to upload file.")

                return 1
        except Exception as e:
            print("Unsuccessful copy.")

            return 1

        return 0

    def s3loccp(self, cloud_path: str, local_path: str):
        try:
            # check the cloud path
            tokenized_cloud_path = self.current_cloud_directory(
                cloud_path).split('/')
            bucket_name = tokenized_cloud_path[1] if len(
                tokenized_cloud_path) > 1 else "/"

            # check bucket exists
            if self.check_bucket_exists('/'.join(tokenized_cloud_path)) == False:
                print("Bucket provided doesn't exist.")
                return 1

            # check local path
            local_file = ""
            if local_path.startswith("/") == True and os.path.exists(local_path) == False and local_file.find('.') != -1:
                # absolute path
                local_file = local_path
            elif local_path.startswith("/") == False and os.path.exists(local_path) == False and local_file.find('.') != -1:
                # relative path
                local_file = os.path.abspath(local_path)
            else:
                print("Local path provided exists or you didn't provide a file name.")
                return 1

            # create object path
            object_path = '/'.join(tokenized_cloud_path[2:])

            try:
                s3_client = self.s3.client('s3')

                key_count = s3_client.list_objects_v2(
                    Bucket=bucket_name, Prefix=object_path)['KeyCount']
                if key_count != 1:
                    print("This file doesn't exist!")
                    return 1

                # download file to S3 bucket
                s3_client.download_file(bucket_name, object_path, local_file)
            except OSError as e:
                print("No such file or directory.")
                return 1
            except Exception as e:
                print("Failed to download file.")

                return 1
        except:
            print("Unsuccessful copy.")

            return 1

        return 0

    def create_folder(self, cloud_path: str):
        try:
            # check the cloud path
            tokenized_cloud_path = self.current_cloud_directory(
                cloud_path).split('/')
            bucket_name = tokenized_cloud_path[1] if len(
                tokenized_cloud_path) > 1 else "/"

            if self.check_bucket_exists('/'.join(tokenized_cloud_path)) == False:
                print("Bucket name doesn't exist!")
                return 1

            object_path = '/'.join(tokenized_cloud_path[2:])

            if object_path.find('.') != -1:
                print("Cannot contain periods.")
                return 1

            s3_client = self.s3.client('s3')
            key_count = s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=object_path)['KeyCount']
            if key_count != 0:
                print("This folder already exists!")
                return 1

            try:
                # create folder in bucket
                s3_client.put_object(Bucket=bucket_name, Key=object_path)
                print(f"Folder {object_path} created in bucket {bucket_name}.")
            except:
                print(f"Failed to create folder in {bucket_name}.")

                return 1
        except Exception as e:
            print("Cannot create folder.")

            return 1

        return 0

    def change_cloud_location(self, cloud_path: str):
        # user wants to go to root
        if cloud_path in ["/", "~"]:
            self.cloud_path = ""

            if cloud_path != "~":
                self.cloud_bucket = ""
        elif cloud_path in ['..', "../.."] and len(self.cloud_bucket) != 0:
            for _ in cloud_path.split('/'):
                if self.cloud_path != "" and len(self.cloud_path.split('/')) > 0:
                    # able to pop from cloud_path
                    temp = self.cloud_path.split('/')
                    temp.pop()

                    self.cloud_path = '/'.join(temp)
                elif len(self.cloud_bucket) != 0:
                    # cloud dir is empty and must pop from bucket
                    temp = self.cloud_bucket.split('/')
                    temp.pop()

                    self.cloud_bucket = '/'.join(temp)
        elif cloud_path in ['..', "../.."] and len(self.cloud_bucket) == 0:
            print("Already at root of S3.")

            return 0

        else:
            try:
                # store cloud location as items in list
                curr_path: list = cloud_path.split('/')
                prev_path: list = (f"/{self.cloud_bucket}" if len(self.cloud_path)
                                   == 0 else f"/{self.cloud_bucket}/{self.cloud_path}").split('/')

                # check bucket is valid and exists
                if self.check_bucket_exists(cloud_path) == False and len(self.cloud_bucket) == 0 and cloud_path.startswith('/'):
                    print("Bucket provided doesn't exist.")
                    return 1

                curr_bucket = ""
                object_path = ""
                if cloud_path.startswith('/') and len(curr_path) >= 2:
                    # bucket
                    curr_bucket: str = curr_path[1]
                    object_path: str = '/'.join(curr_path[2:]) or ""
                elif cloud_path.startswith('/') == False and len(curr_path) > 0 and len(self.cloud_bucket) > 0:
                    # relative path
                    object_path: str = '/'.join(curr_path) if len(
                        curr_path) >= 1 and self.cloud_bucket != "" else ""

                # make sure the path only contains folder and not file
                if re.search(r"(\w*\.\w{3,4})", object_path) != None:
                    print(
                        "You have provided a path to a file, please provide a path to a folder.")

                    return 1

                # validate the cloud path against previous path
                valid_path = self.generate_valid_cloud_path(cloud_path)
                prev_path_str = '/'.join(prev_path)

                if valid_path == prev_path_str:
                    print(
                        "Either invalid folder was provided or already in desired directory.")
                else:
                    if self.cloud_bucket != curr_bucket and curr_bucket != "":
                        self.cloud_bucket = curr_bucket

                    self.cloud_path = '/'.join(valid_path.split('/')[2:])

            except Exception as e:
                print("Cannot change folder.")

                return 1

        return 0

    def current_cloud_directory(self, cloud_path: str = ""):
        if cloud_path.startswith('/'):
            # passing in a path with a bucket
            if cloud_path.find('.') != -1:
                # file
                return f"{cloud_path}"
            else:
                return f"{cloud_path.rstrip('/')}/"
        elif len(self.cloud_bucket) == 0 and len(self.cloud_path) == 0:
            if cloud_path.find('.') != -1:
                # file
                return "/" if cloud_path == "" else f"{cloud_path}"
            else:
                return "/" if cloud_path == "" else f"{cloud_path.rstrip('/')}/"
        elif len(self.cloud_bucket) > 0 and len(self.cloud_path) > 0:
            if cloud_path.find('.') != -1:
                # file
                return f"/{self.cloud_bucket.strip('/')}/{self.cloud_path.strip('/')}/" if cloud_path == "" else f"/{self.cloud_bucket.strip('/')}/{self.cloud_path.strip('/')}/{cloud_path}"
            else:
                return f"/{self.cloud_bucket.strip('/')}/{self.cloud_path.strip('/')}/" if cloud_path == "" else f"/{self.cloud_bucket.strip('/')}/{self.cloud_path.strip('/')}/{cloud_path.rstrip('/')}/"
        elif len(self.cloud_bucket) > 0 and len(self.cloud_path) == 0:
            if cloud_path.find('.') != -1:
                # file
                return f"/{self.cloud_bucket.strip('/')}/" if cloud_path == "" else f"/{self.cloud_bucket.strip('/')}/{cloud_path}"
            else:
                return f"/{self.cloud_bucket.strip('/')}/" if cloud_path == "" else f"/{self.cloud_bucket.strip('/')}/{cloud_path.rstrip('/')}/"

        return ""

    def print_current_cloud_directory(self):
        if self.current_cloud_directory() == "":
            return 1
        else:
            print(self.current_cloud_directory().rstrip('/'))

    def list_cloud_directory(self, cloud_path: str, l_flag: bool):
        try:
            # handle for -l flag
            tokenized_cloud_path = cloud_path.split("/")

            # self.generate_valid_cloud_path(cloud_path)
            abs_cloud_path = self.current_cloud_directory(
                cloud_path)

            # handle cases
            if len(abs_cloud_path) <= 1 or self.check_bucket_exists(abs_cloud_path) == False:
                # bucket case
                print("Buckets in S3:")
                [print(bucket) for bucket in self.get_bucket_names()]
            else:
                # check directory passed exists
                if self.directory_exists_in_cloud(abs_cloud_path) == False and abs_cloud_path.startswith('/') == False:
                    print("Directory doesn't exist!")

                    return 1

                tokenized_cloud_path = abs_cloud_path.split("/")
                s3_client = self.s3.client("s3")

                # handle prefix setting
                prefix = "" if len(
                    '/'.join(tokenized_cloud_path[2:])) == 0 else f"{'/'.join(tokenized_cloud_path[2:]).rstrip('/')}/"

                # retrieve objects in bucket
                objects = s3_client.list_objects_v2(
                    Bucket=tokenized_cloud_path[1], Prefix=prefix)

                objects_to_print = [] if objects['KeyCount'] == 0 else objects['Contents']

                # l_flag prints size, type, and permissions
                if len(objects_to_print) == 0:
                    print("This bucket or directory is empty.")
                else:
                    print("|Item|") if l_flag == False else print(
                        "|Item|\t|Type|\t|Size|\t|Permissions|")

                    for obj in objects_to_print:
                        if l_flag:
                            # Additional file data
                            obj_metadata = (s3_client.head_object(
                                Bucket=tokenized_cloud_path[1], Key=obj['Key']))['ResponseMetadata']
                            obj_http_data = obj_metadata['HTTPHeaders']

                            # File permissions
                            obj_acl = (s3_client.get_object_acl(
                                Bucket=tokenized_cloud_path[1], Key=obj['Key']))['Grants']
                            obj_permissions = obj_acl[0]
                            print(
                                f"|{obj['Key']}|\t|{obj_http_data['content-type']}|\t|{obj['Size']}|\t|{obj_permissions['Permission']}|")
                        else:
                            print(f"|{obj['Key']}|")

        except Exception as e:
            print("Cannot list contents of this S3 location.")
            return 1

        return 0

    def s3_copy(self, src_cloud_path: str, dst_cloud_path: str):
        try:
            valid_src = self.generate_valid_cloud_path(src_cloud_path)
            valid_dst = self.generate_valid_cloud_path(dst_cloud_path, True)

            # checks src and dst have valid buckets
            if self.check_bucket_exists(valid_src) == False:
                print("Invalid source bucket passed.")
            elif self.check_bucket_exists(valid_dst) == False:
                print("Invalid destination bucket passed.")

            tokenized_src_cloud_path = valid_src.split('/')
            tokenized_dst_cloud_path = valid_dst.split('/')

            src_bucket = tokenized_src_cloud_path[1]
            dst_bucket = tokenized_dst_cloud_path[1]
            copy_src_object_path = '/'.join(tokenized_src_cloud_path[2:])
            copy_dst_object_path = '/'.join(tokenized_dst_cloud_path[2:])

            src_obj = '/'.join(tokenized_src_cloud_path[2:])
            dst_obj = '/'.join(tokenized_dst_cloud_path[2:])

            src_bucket_objs = self.objects_in_bucket(valid_src)
            dst_bucket_objs = self.objects_in_bucket(valid_dst)

            # check src obj exists and dst doesn't
            if src_obj not in src_bucket_objs:
                print("Source object doesn't exist in source bucket!")
                return 1
            elif dst_obj in dst_bucket_objs:
                print("Destination object exists in destination bucket!")
                return 1

            try:
                s3_client = self.s3.client('s3')
                s3_client.copy_object(
                    Bucket=dst_bucket, Key=copy_dst_object_path, CopySource={'Bucket': src_bucket, "Key": copy_src_object_path})

                print(
                    f"Successfully copied object from {src_bucket} bucket to {dst_bucket} bucket.")
            except Exception as e:
                print("Something went wrong during copy.")
                return 1
        except Exception as e:
            print("Cannot perform copy.")
            return 1

        return 0

    def s3_delete(self, cloud_path: str):
        try:
            tokenized_cloud_path = self.current_cloud_directory(
                cloud_path).split('/')
            bucket_name = tokenized_cloud_path[1] if len(
                tokenized_cloud_path) > 1 else "/"

            if self.check_bucket_exists('/'.join(tokenized_cloud_path)) == False:
                print("Bucket name doesn't exist!")
                return 1

            object_path: str = '/'.join(tokenized_cloud_path[2:])

            s3_client = self.s3.client('s3')

            # check folder is empty if folder is passed
            try:
                key_count = s3_client.list_objects_v2(
                    Bucket=bucket_name, Prefix=object_path)['KeyCount']

                if key_count == 0:
                    print("This object does not exist!")
                    return 1
                elif key_count > 1:
                    print("This folder isn't empty!")
                    return 1
            except Exception as e:
                print("The bucket or the directory might be invalid.")
                return 1

            try:
                s3_client.delete_object(Bucket=bucket_name, Key=object_path)

                print(f"Successfully deleted object from {bucket_name}.")
            except Exception as e:
                print("Something went wrong trying to delete object.")
                return 1
        except Exception as e:
            print("Cannot perform delete.")
            return 1

        return 0

    def change_dir_local(self, local_path):
        try:
            # handle ..
            if '..' in local_path.split('/'):
                # get current dir
                curr_dir = os.path.abspath(os.curdir)

                for _ in local_path.split('/'):
                    # remove a directory item from the list for each ".."
                    temp = curr_dir.split('/')
                    temp.pop()
                    curr_dir = '/'.join(temp)

                os.chdir(os.path.abspath(curr_dir))
            elif '~' == local_path:
                os.chdir(os.path.expanduser('~'))
            elif '/' == local_path:
                os.chdir('/')
            else:
                # change to folder
                curr_dir = os.path.abspath(local_path)
                if os.path.exists(curr_dir) and os.path.isdir(curr_dir):
                    os.chdir(os.path.abspath(curr_dir))

        except:
            print("Unable to change to specified directory.")
            return 1

        return 0

    def list_directory_local(self):
        try:
            [print(item, end="  ") for item in os.listdir()]
            print()
        except:
            print("Unable to list items in current directory.")
            return 1

        return 0

    def current_working_dir_local(self):
        try:
            print(os.path.abspath(os.curdir))
        except:
            print("Unable to print current working directory.")
            return 1

        return 0


if __name__ == "__main__":
    s5 = S5()
    s5.start()
