import glob, os
import urllib
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

    def return_type_as_string(self, in_var):
        if type(in_var) == float:
            return "double"
        elif type(in_var) == str:
            return "string"
        elif type(in_var) == int:
            return "integer"

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

    def deep_indexing_general_mat(self, in_mat):
        # create output json folder 
        output_folder_name = "./output_json/"
        if not os.path.exists(output_folder_name):
            os.makedirs(output_folder_name)
        #read_general_mat(in_mat, self.session)

        print("4.1 Generate JSON for the general .MAT File--------------------------")

        # check whether current working directory is the folder containing data files 
        subfolder_check = r"\download_files"
        if subfolder_check not in os.getcwd():
            os.chdir("./download_files")

        overall_mat = loadmat(in_mat['rawDataFile']['fileName'])

        # go inside the data filed of the data 
        dt = overall_mat['subsets']['data']
        dim_m, dim_n = dt.shape
        # test corners start from the 9th row, 8 rows for metadata and keywords 
        test_corners_start = 8
        
        num_params = np.count_nonzero(dt[0,:] == 'param')
        # get the column index of the out 
        index_out = np.where(dt[0,:] == 'out')
        index_aux = np.where(dt[0,:] == 'aux')

        # create output file, have to move one folder up, have to move one folder up
        output_file_path = '../output_json/' + in_mat['rawDataFile']['fileName'].replace('.mat' , '.json')

        # multiple blocks should be inside a array struct
        array_block = {}
        array_block['deepIndexing'] = []

        first_json_write = {}
        first_json_write['internalMetadata'] = {}
        first_json_write['internalMetadata']['deepIndexing'] = array_block['deepIndexing']


        with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(first_json_write, outfile, indent=4)

        conditions_mat = []
        for idx in range(test_corners_start, dim_m): # number of test corners
            # construct condition block 
            condition_mat = []
            for num_param in range(num_params): # number of params 
                cond_dict ={}
                cond_dict['name'] = dt[7, 1 + num_param]
                cond_dict['value'] = str(dt[idx, 1 + num_param])
                cond_dict['unit'] = dt[6, 1 + num_param]
                condition_mat.append(cond_dict)  
            conditions_mat.append(condition_mat)
            # print(conditions_mat[5]) #out: [{'name': 'tambient', 'value': -40, 'unit': 'C'}, {'name': 'Vsup', 'value': 13.5, 'unit': 'V'}, {'name': 'Iload', 'value': 0.1, 'unit': 'A'}]  
            
            # construct channel block 
            # out:{'channel': {'metadata': {'name': 'Reg2', 'type': 'integer'}}, 'pathtype': 'atv_ps_mat', 'pathspec': 'subsets.data{9,6}'}
            
            out_json = {}  
            out_json['artifact_metadata'] = {}
            #out_json['artifact_metadata']['artifact_id'] = "This is the Nr." + str(idx-7) + " test corner."
            out_json['artifact_metadata']['artifact_id'] = in_mat['artifactID']
            out_json['artifact_metadata']['username'] = "Xing Jin"
            out_json['artifact_metadata']['source'] = "local test"
            out_json['artifact_metadata']['filetype'] = "atv-ps-mat"

            out_json['metadata'] = {}
            out_json['metadata']['timestamp'] = in_mat['dateCreated']

            out_json['operating_conditions'] = {}
            out_json['operating_conditions'] = condition_mat

            #loop over all out
            for idx_out in index_out[0]:
                out_json['channel'] = {}
                channel_metadata={}
                # since name of the out is in the 7th row
                channel_metadata['name'] = dt[7, idx_out]
                channel_metadata['type'] = self.return_type_as_string(dt[idx, idx_out])

                out_json['channel']['metadata'] = channel_metadata
                out_json['channel']['pathtype'] = "atv_ps_mat"
                out_json['channel']['pathspec'] = "subsets.data{" + str(idx+1) + "," + str(idx_out+1) + "}"

                with open(output_file_path, "r+") as outfile:
                    data = json.load(outfile)
                    #data.update(out_json)
                    data['internalMetadata']['deepIndexing'].append(out_json) #first_json_write['deepIndexing'].append(out_json)
                    outfile.seek(0)
                    json.dump(data, outfile, indent=4)

            #loop over all aux
            for idx_aux in index_aux[0]:
                out_json['channel'] = {}
                channel_metadata={}
                # since name of the out is in the 7th row
                channel_metadata['name'] = dt[7, idx_aux]
                channel_metadata['type'] = self.return_type_as_string(dt[idx, idx_aux])

                out_json['channel']['metadata'] = channel_metadata
                out_json['channel']['pathtype'] = "atv_ps_mat"
                out_json['channel']['pathspec'] = "subsets.data{" + str(idx+1) + "," + str(idx_aux+1) + "}"

                with open(output_file_path, "r+") as outfile:
                    data = json.load(outfile)
                    #data.update(out_json)
                    data['internalMetadata']['deepIndexing'].append(out_json) #first_json_write['deepIndexing'].append(out_json)
                    outfile.seek(0)
                    json.dump(data, outfile, indent=4)


        with open(output_file_path, "r+") as outfile:
        
            data = json.load(outfile)
            #print("9. Updating-------------------")

            artifact_id = in_mat['artifactID']
            # metadata = {
            #     "Hi": "again !"
            # }
            metadata = data

            data = {
            'metadata': json.dumps(metadata)
            }
            
            metadata_url_encoded = urllib.parse.urlencode(data, quote_via=urllib.parse.quote) # Url encode the metadata

            os.chdir("..")


            base_url = 'https://rd-datalake.icp.infineon.com'
            project_key= 'RDDLTST1'

            response = self.session.post(f'{base_url}/v1/projects/{project_key}/artifacts/{artifact_id}/metadata/version',
                                    headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=metadata_url_encoded)

            artifact_metadata = json.loads(response.text)
            print('Response Received: ' + str(response.status_code) + ': ' + json.dumps(artifact_metadata, indent=4))

    def deep_indexing_wfm_mat(self,in_mat):
        # create output json folder 
        output_folder_name = "./output_json/"
        if not os.path.exists(output_folder_name):
            os.makedirs(output_folder_name)
        #read_waveform_mat(in_mat, self.session)

        # check whether current working directory is the folder containing data files 
        subfolder_check = r"\download_files"
        if subfolder_check not in os.getcwd():
            os.chdir("./download_files")

        wfm_mat = loadmat(in_mat['rawDataFile']['fileName'])

        dt = wfm_mat['data']
        # create output file with the name of the test project and conditions
        output_file_path = '../output_json/' + in_mat['rawDataFile']['fileName'].replace('.mat' , '.json')

        # multiple blocks should be inside a array struct
        array_block = {}
        array_block['deepIndexing'] = []

        first_json_write = {}
        first_json_write['internalMetadata'] = {}
        first_json_write['internalMetadata']['deepIndexing'] = array_block['deepIndexing']

        with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(first_json_write, outfile, indent=4)

        # get conditions for the current test corner 
        dt_params = dt['param']
        condition_mat = []

        for key_cond in dt_params.keys():
            #iterate over all conditions 
            dt_params_middle = dt_params[key_cond]
            cond_dict ={}
            cond_dict['name'] = key_cond
            cond_dict['value'] = str(dt_params_middle['value'])
            cond_dict['unit'] = dt_params_middle['unit']
            condition_mat.append(cond_dict)  

        # construct other fields 
        out_json = {}  
        out_json['artifact_metadata'] = {}
        #out_json['artifact_metadata']['artifact_id'] = "This is the Nr. 1 test corner."
        out_json['artifact_metadata']['artifact_id'] = in_mat['artifactID']
        out_json['artifact_metadata']['username'] = "Xing Jin"
        out_json['artifact_metadata']['source'] = "local test"
        out_json['artifact_metadata']['filetype'] = "atv-ps-wfm"

        out_json['metadata'] = {}
        out_json['metadata']['timestamp'] = in_mat['dateCreated']

        out_json['operating_conditions'] = {}
        out_json['operating_conditions'] = condition_mat

        # construct channle field 
        dt_out = dt['out']
        #loop over all out
        for key_out in dt_out.keys():
            out_json['channel'] = {}
            channel_metadata={}
            dt_out_middle = dt_out[key_out]
            # since name of the out is in the 7th row
            channel_metadata['name'] = key_out
            channel_metadata['type'] = self.return_type_as_string(dt_out_middle['value'])

            out_json['channel']['metadata'] = channel_metadata
            out_json['channel']['pathtype'] = "atv_ps_wfm"
            out_json['channel']['pathspec'] = "data{1, 1}.out." + str(key_out)

            # append current block into json 
            with open(output_file_path, "r+") as outfile:
                data = json.load(outfile)
                #data.update(out_json)
                data['internalMetadata']['deepIndexing'].append(out_json) #first_json_write['deepIndexing'].append(out_json)
                outfile.seek(0)
                json.dump(data, outfile, indent=4)

        with open(output_file_path, "r+") as outfile:
            
            data = json.load(outfile)
            #print("9. Updating-------------------")

            artifact_id = in_mat['artifactID']
            # metadata = {
            #     "Hi": "again !"
            # }
            metadata = data

            data = {
            'metadata': json.dumps(metadata)
            }
            
            metadata_url_encoded = urllib.parse.urlencode(data, quote_via=urllib.parse.quote) # Url encode the metadata

            os.chdir("..")


            base_url = 'https://rd-datalake.icp.infineon.com'
            project_key= 'RDDLTST1'

            response = self.session.post(f'{base_url}/v1/projects/{project_key}/artifacts/{artifact_id}/metadata/version',
                                    headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=metadata_url_encoded)

            artifact_metadata = json.loads(response.text)
            print('Response Received: ' + str(response.status_code) + ': ' + json.dumps(artifact_metadata, indent=4))

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