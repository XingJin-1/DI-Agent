import time

import glob, os
import numpy as np
import json
import shutil
import pathlib
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import warnings

from DI import Deep_Indexing_Agent
from loadMATLib import loadmat


MEGA = 10 ** 6
MEGA_STR = ' ' * MEGA

def init():
    print('Init called')


def process(data):
    # print('Experiment started, Artifact URL: {}, Metadata: {}'.format(
    # data['url'],
    # data['metadata']
    # ), flush=True)

    base_url = 'https://rd-datalake.icp.infineon.com'
    project_key= 'RDDLTST1'

    deep_Indexing_Agent = Deep_Indexing_Agent(base_url, project_key)

    deep_Indexing_Agent.connect_to_DL()
    deep_Indexing_Agent.download_files_single(data)

    subfolder_check = r"\download_files"
    if subfolder_check not in os.getcwd():
        os.chdir("./download_files")
    overall_mat = loadmat(data['rawDataFile']['fileName'])
    os.chdir("..")

    # create output json folder 
    output_folder_name = "./output_json/"
    if not os.path.exists(output_folder_name):
        os.makedirs(output_folder_name)

    if 'subsets' in overall_mat.keys():
        deep_Indexing_Agent.deep_indexing_general_mat(data)
    else:
        deep_Indexing_Agent.deep_indexing_wfm_mat(data)

    time.sleep(5)

    print("Experiment finished", flush=True)

def post_process():
    print('Post processing called')


def main():
    data={}
    data['DataType'] = "MATLAB"
    data['TestName'] = "Serverless_Testing_For_DI_Agent"
    data['artifactID'] = "9f4f5be0b26b47e48762ab3c949a3014"
    data['dateCreated'] = "2021-06-14T22:02:15Z"

    rawDataFileField = {}
    rawDataFileField['contentType'] = "application/octet-stream"
    rawDataFileField['fileName'] = "mat_plus_new_metadata_sample=1[]_tambient=-40[C]_Vsup=28[V]_Iload=0.1[A]_REP=00001[].mat"
    rawDataFileField['fileSize'] = "3965"
    data['rawDataFile'] = rawDataFileField

    data['version'] = "1"

    process(data)

if __name__ == "__main__":
    main()