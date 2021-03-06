#!/usr/bin/env python

import shutil
import urllib
import os
import sys
import json
import time
from random import randint
import subprocess
from utils import get_task_dict, save_output_json

task_dict = get_task_dict(sys.argv[1])
cwd = os.getcwd()

"""
    input:
      donor:
        type: string
      vcflist:
        type: array
      normal_id:
        type: string
      tumours:
        type: dict

"""
donor = task_dict.get('input').get('donor')
refUrl = task_dict.get('input').get('refUrl')
normal_id = task_dict.get('input').get('normal_id')
tumours= task_dict.get('input').get('tumours')
refdone = False

task_start = int(time.time())

try:

    #ref file download
    if os.path.isfile("public_full9.tar.gz") == False:
        #current_dir = os.path.dirname(os.path.realpath(__file__)) #for storing ref data on worker. not complete yet
        #target_dir = os.path.sep.join(current_dir.split(os.path.sep)[:-2])
        os.mkdir("ref")
        print(subprocess.check_output(['wget', '-O', 'public_full9.tar.gz', refUrl]))
        print(subprocess.check_output(['tar', 'xvzf', 'public_full9.tar.gz', '--directory', 'ref']))
        os.remove("public_full9.tar.gz")

    refdir = os.path.abspath("ref")

    out_tumour =[]
    out_vcf = []
    os.mkdir(donor)
    dirpath = os.path.abspath(donor)
    #normalBam
    r = subprocess.check_output(['icgc-storage-client', '--profile', 'collab', 'download', '--object-id', str(list(normal_id.values())[0]), '--output-dir', donor])
    #horrible way to try to get keys of a dict but others did not work. takes all keys, converts to list and take first element
    out_bam = str(list(normal_id.keys())[0])

    #Parse through tumours
    for t in tumours:
        #probably a better way to do this
        bamObjID = str(list(t["bamFileName"].values())[0])
        bamNames = str(list(t["bamFileName"].keys())[0])
        out_tumour.append(bamNames)
        f = subprocess.check_output(['icgc-storage-client', '--profile', 'collab', 'download', '--object-id', bamObjID, '--output-dir', donor])
        # in case file downloaded has a bad name
        if os.path.isfile(os.path.join(donor, bamObjID)) and os.path.isfile(os.path.join(donor, bamNames)) == False:
            os.rename(os.path.join(donor, bamObjID), os.path.join(donor, bamNames))

        for i in list(t['associatedVcfs'].keys()):
            vcfKey = str(i)
            vcfObjID = t['associatedVcfs'].get(vcfKey)
            out_vcf.append(vcfObjID)
            k = subprocess.check_output(['icgc-storage-client', '--profile', 'collab', 'download', '--object-id', vcfObjID, '--output-dir', donor])
            # rename in case file name bad
            if os.path.isfile(os.path.join(donor, vcfObjID)) and os.path.isfile(os.path.join(donor, vcfKey)) == False:
                os.rename(os.path.join(donor, vcfObjID), os.path.join(donor, vcfKey))

    #use for fast testing
    # open(donor + '/' + str(list(normal_id.keys())[0]), 'a').close()
    #
    # for t in tumours:
    #     bamObjID = str(list(t["bamFileName"].values())[0])
    #     bamNames = str(list(t["bamFileName"].keys())[0])
    #     out_tumour.append(bamNames)
    #     open(donor + '/' + (str(list(t["bamFileName"].keys())[0])), 'a').close()
    #
    #     for i in list(t['associatedVcfs'].keys()):
    #         vcfKey = str(i)
    #         vcfObjID = t['associatedVcfs'].get(vcfKey)
    #         out_vcf.append(vcfObjID)
    #         open(donor + '/' + (str(i)), 'a').close()

except Exception, e:
    #if failure I dont want data crowding the job and worker
    with open('jt.log', 'w') as f: f.write(str(e))
    if os.path.isfile("public_full9.tar.gz"):
        os.remove("public_full9.tar.gz")

    if os.path.isdir("ref"):
        shutil.rmtree("ref")

    if os.path.isdir(donor):
        shutil.rmtree(donor)
    sys.exit(1)  # task failed


# complete the task

task_stop = int(time.time())

output_json = {
    'bam': out_bam,
    'tumour_bam': out_tumour,
    'vcf': out_vcf,
    'dir_path': dirpath,
    'ref_path': refdir
}

save_output_json(output_json)
