#!/usr/bin/env python

import subprocess as sp
import numpy as np
import os

CLUSTER = True

if __name__ =="__main__":

    # root dir to store all results
    work_dir = "./flu_H3N2/subtree_samples"

    #sub-directories and file names
    out_dir = os.path.join(work_dir, "2017-04-20")
    treetime_res_file = os.path.join(work_dir, "2017-04-20_treetime_res.csv")
    lsd_res_file = os.path.join(work_dir, "2017-04-20_lsd_res.csv")

    # LSD run configuration
    lsd_parameters = ['-c', '-r', 'a', '-v']

    n_iter = 20
    N_leaves_array = [20, 50, 100, 200, 500, 750, 1000, 1250, 1500, 1750, 2000]

    for N_leaves in N_leaves_array:
        for iteration in np.arange(n_iter):
            subtree_fname_suffix = str(iteration)

            if CLUSTER:
                call = ['qsub', '-cwd', '-b','y',
                        '-l', 'h_rt=23:59:0',
                        #'-o', './stdout.txt',
                        #'-e', './stderr.txt',
                        '-l', 'h_vmem=50G',
                        './generate_flu_subtrees_dataset_run.py']

            else:
                call = ['./generate_flu_subtrees_dataset_run.py']


            arguments = [
                str(N_leaves),
                out_dir,
                subtree_fname_suffix,
                treetime_res_file,
                lsd_res_file
            ]

            call.extend(arguments)
            sp.call(call)