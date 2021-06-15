import os 
import urllib
import numpy as np
import json
import shutil
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import warnings

from readMAT import return_type_as_string
from loadMATLib import loadmat



def read_waveform_mat(in_mat_file, in_session):
    # check whether current working directory is the folder containing data files 
    subfolder_check = r"\download_files"
    if subfolder_check not in os.getcwd():
        os.chdir("./download_files")

    wfm_mat = loadmat(in_mat_file['rawDataFile']['fileName'])

    dt = wfm_mat['data']
    # create output file with the name of the test project and conditions
    output_file_path = '../output_json/' + in_mat_file['rawDataFile']['fileName'].replace('.mat' , '.json')

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
    out_json['artifact_metadata']['artifact_id'] = in_mat_file['artifactID']
    out_json['artifact_metadata']['username'] = "Xing Jin"
    out_json['artifact_metadata']['source'] = "local test"
    out_json['artifact_metadata']['filetype'] = "atv-ps-wfm"

    out_json['metadata'] = {}
    out_json['metadata']['timestamp'] = in_mat_file['dateCreated']

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
        channel_metadata['type'] = return_type_as_string(dt_out_middle['value'])

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

        artifact_id = in_mat_file['artifactID']
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

        response = in_session.post(f'{base_url}/v1/projects/{project_key}/artifacts/{artifact_id}/metadata/version',
                                headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=metadata_url_encoded)

        artifact_metadata = json.loads(response.text)
        print('Response Received: ' + str(response.status_code) + ': ' + json.dumps(artifact_metadata, indent=4))
        