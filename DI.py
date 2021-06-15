import glob, os
import numpy as np
import json
import shutil
import pathlib
import time
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import warnings

warnings.filterwarnings('ignore')

from loadMATLib import loadmat
from alive_progress import alive_bar
from readMAT import read_general_mat
from readWfm import read_waveform_mat

# Paths to the root of the project and the `data` subfolder.
PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
DATA_ROOT = PROJECT_ROOT / 'testDataFolder'

class Deep_Indexing_Agent:
    def __init__(self, base_url, project_key):
        self.base_url = base_url
        self.project_key = project_key
        self.session = requests.session()
        self.session.verify = "ca-bundle.crt"

    def connect_to_DL(self):
        print("1. Connecting-------------------")

        response = self.session.get(f'{self.base_url}/v1/oauth/token', auth=HttpNegotiateAuth())
        print(f'Status: {response.status_code}\nText: {response.text}')

        token = json.loads(response.text)
        headers = {
            'accept': 'application/json',
            'Authorization': "Bearer {}".format(token['access_token'])
        }
        self.session.headers.update(headers)

    def download_files(self):
        print("3. Downloading-------------------")
        # currently inside the root directory 

        # create folder for the storing downlowded data 
        downlaod_file_folder_name = "./download_files/"
        if not os.path.exists(downlaod_file_folder_name):
            os.makedirs(downlaod_file_folder_name)

        # get all to be downloaded files
        gen_mat_file = {}
        wfm_mat_files = {}
        with open('upload_files.json', "r") as uploaded_json:
            data = json.load(uploaded_json)
            gen_mat_file = data['general_mat']
            wfm_mat_files = data['wfm_mat']

        list_mat_files = []
        list_mat_files = wfm_mat_files
        list_mat_files.append(gen_mat_file)
        # dont need to distinguish general and wfm .mat files here 
        with alive_bar(len(list_mat_files)) as bar:
            for mat_file in list_mat_files:
                bar()

                local_filename = mat_file['file_name']
                artifact_id = mat_file['mat_id']
                response = self.session.get(f'{self.base_url}/v1/projects/{self.project_key}/artifacts/{artifact_id}', stream=True)
                response.raw.decode_content = True
                with open('./download_files/' + local_filename, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                #print('Response Received: ' + str(response.status_code))

                time.sleep(0.1)
        # until this part, all .mat has been downloaded to the /download_files folder and license was copied into it--> used for the api request 

    def download_files_single(self, input_data):
        # create folder for the storing downlowded data 
        downlaod_file_folder_name = "./download_files/"
        if not os.path.exists(downlaod_file_folder_name):
            os.makedirs(downlaod_file_folder_name)

        mat_file = input_data

        local_filename = mat_file['rawDataFile']['fileName']
        artifact_id = mat_file['artifactID']

        response = self.session.get(f'{self.base_url}/v1/projects/{self.project_key}/artifacts/{artifact_id}', stream=True)
        response.raw.decode_content = True
        with open('./download_files/' + local_filename, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

    def deep_indexing_operaiton(self):
        print("4. Read Files -------------------")
        # currently inside the root directory 

        # create output json folder 
        output_folder_name = "./output_json/"
        if not os.path.exists(output_folder_name):
            os.makedirs(output_folder_name)

        # get all downloaded and to be analyzed files
        with open('upload_files.json', "r") as uploaded_json:
            data = json.load(uploaded_json)
            gen_mat_file = data['general_mat']
            wfm_mat_files = data['wfm_mat']

        read_general_mat(gen_mat_file)

        print("4.2 Generate JSON for the Wavefrom .MAT File--------------------------") 
        with alive_bar(len(wfm_mat_files)) as bar:
            # create json for general .mat file 
            # create json for waveform .mat files 
            for i in range(len(wfm_mat_files)):
                bar()
                read_waveform_mat(wfm_mat_files[i])
                time.sleep(0.1)

        os.chdir("..")

    # def delete_files(self):
    #     print("5. Deleting-------------------")
    #     # list_mat_id gets from uploading procedure 
    #     for arti_id in list_mat_id:
    #         #artifact_id = '4a928ba978aa4e0787757cb6ee69dd1a'
    #         artifact_id = arti_id
    #         response = self.session.delete(f'{self.base_url}/v1/projects/{self.project_key}/artifacts/{artifact_id}')
    #         print('Response Received: ' + str(response.status_code) + ': ' + response.text)

    def deep_indexing_general_mat(self,in_mat):
        # create output json folder 
        output_folder_name = "./output_json/"
        if not os.path.exists(output_folder_name):
            os.makedirs(output_folder_name)
        read_general_mat(in_mat,self.session)

    def deep_indexing_wfm_mat(self,in_mat):
        # create output json folder 
        output_folder_name = "./output_json/"
        if not os.path.exists(output_folder_name):
            os.makedirs(output_folder_name)
        read_waveform_mat(in_mat,self.session)

def main():

    print("PROJECT_ROOT: ", PROJECT_ROOT)
    print("DATA_ROOT: ", DATA_ROOT)
    
    base_url = 'https://aimlms.muc-gp.icp.infineon.com'
    project_key = 'AIMLTST2'

    deep_Indexing_Agent = Deep_Indexing_Agent(base_url, project_key)
    deep_Indexing_Agent.connect_to_DL()
    deep_Indexing_Agent.download_files()
    deep_Indexing_Agent.deep_indexing_operaiton()

    # with open('upload_files.json', "r") as uploaded_json:
    #         data = json.load(uploaded_json)
    #         gen_mat_file = data['general_mat']

    # subfolder_check = r"\download_files"
    # if subfolder_check not in os.getcwd():
    #     os.chdir("./download_files")
    # overall_mat = loadmat(gen_mat_file['file_name'])

    # if 'subsets' in overall_mat.keys():
    #     print(1)
    # else:
    #     print(0)

# if __name__ == "__main__":
#     main()

# def main(data):

#     download_files(data["url"])

#     deep_indexing_operaiton()