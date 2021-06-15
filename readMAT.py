import os 
import urllib
import numpy as np
import json
import shutil
import requests
from requests_negotiate_sspi import HttpNegotiateAuth
import warnings


from loadMATLib import loadmat


def return_type_as_string(in_var):
    if type(in_var) == float:
        return "double"
    elif type(in_var) == str:
        return "string"
    elif type(in_var) == int:
        return "integer"

def read_general_mat(in_mat_file, in_session):
    print("4.1 Generate JSON for the general .MAT File--------------------------")

    # check whether current working directory is the folder containing data files 
    subfolder_check = r"\download_files"
    if subfolder_check not in os.getcwd():
        os.chdir("./download_files")

    overall_mat = loadmat(in_mat_file['rawDataFile']['fileName'])

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
    output_file_path = '../output_json/' + in_mat_file['rawDataFile']['fileName'].replace('.mat' , '.json')

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
        out_json['artifact_metadata']['artifact_id'] = in_mat_file['artifactID']
        out_json['artifact_metadata']['username'] = "Xing Jin"
        out_json['artifact_metadata']['source'] = "local test"
        out_json['artifact_metadata']['filetype'] = "atv-ps-mat"

        out_json['metadata'] = {}
        out_json['metadata']['timestamp'] = in_mat_file['dateCreated']

        out_json['operating_conditions'] = {}
        out_json['operating_conditions'] = condition_mat

        #loop over all out
        for idx_out in index_out[0]:
            out_json['channel'] = {}
            channel_metadata={}
            # since name of the out is in the 7th row
            channel_metadata['name'] = dt[7, idx_out]
            channel_metadata['type'] = return_type_as_string(dt[idx, idx_out])

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
            channel_metadata['type'] = return_type_as_string(dt[idx, idx_aux])

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
