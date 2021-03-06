"""
Plot figures for the TreeTime validation, comparison with other methods on the
simulated dataset.

To plot the validation results,  CSV files generated by the
'generate_simulated_data.py' script are required.

The script plots the reconstruction of the mutation rate and the tiome of the
most recent common ancestor in comparison with other methods (LSD, BEAST)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as mplcm
import matplotlib.colors as colors
import os, sys
import pandas
from Bio import Phylo

import utility_functions_beast as beast_utils
import utility_functions_simulated_data as sim_utils

from plot_defaults import *

def read_treetime_results_csv(fname):
    """
    Read results of the TreeTime simulations

    Args:
     - fname: path to the input file

    Returns:
     - df: Table of results as pandas data-frame
    """

    columns = ['File', 'Sim_Tmrca', 'Tmrca', 'mu', 'R', 'R2_int']
    df = pandas.read_csv(fname, names=columns,header=0)

    #filter obviously failed simulations
    df = df[[len(str(k)) > 10 for k in df.File]]
    df = df[df.R > 0.1]

    # some very basic preprocessing
    df['dTmrca'] = -(df['Sim_Tmrca'] - df['Tmrca'])
    df['Sim_mu'] = map(lambda x: float(x.split("/")[-1].split('_')[6][2:]), df.File)
    df['Ns'] = map(lambda x: int(x.split("/")[-1].split('_')[3][2:]), df.File)
    df['Ts'] = map(lambda x: int(x.split("/")[-1].split('_')[4][2:]), df.File)
    df['N'] = map(lambda x: int(x.split("/")[-1].split('_')[2][1:]), df.File)
    df['T'] = df['Ns']*df['Ts']
    df['Nmu'] = (df['N']*df['Sim_mu'])

    return df

def read_lsd_results_csv(fname):
    """
    Read results of the LSd simulations

    Args:
     - fname: path to the input file

    Returns:
     - df: Table of results as pandas data-frame
    """

    columns = ['File', 'Sim_Tmrca', 'Tmrca', 'mu', 'obj']
    df = pandas.read_csv(fname, names=columns,header=0)

    # Filter out obviously wrong data
    df = df[[len(k) > 10 for k in df.File]]

    #Some basic preprocessing
    df['dTmrca'] = -(df['Sim_Tmrca'] - df['Tmrca'])
    df['Sim_mu'] = map(lambda x: float(x.split("/")[-1].split('_')[6][2:]), df.File)
    df['Ns'] = map(lambda x: int(x.split("/")[-1].split('_')[3][2:]), df.File)
    df['Ts'] = map(lambda x: int(x.split("/")[-1].split('_')[4][2:]), df.File)
    df['N'] = map(lambda x: int(x.split("/")[-1].split('_')[2][1:]), df.File)
    df['T'] = df['Ns']*df['Ts']
    df['Nmu'] = (df['N']*df['Sim_mu'])

    return df

def read_beast_results_csv(fname):
    """
    Read results of the BEAST simulations

    Args:
     - fname: path to the input file

    Returns:
     - df: Table of results as pandas data-frame
    """

    columns = ['File', 'N', 'Sim_Tmrca', 'Sim_mu', 'Ns', 'Ts', 'T', 'Nmu',
                'LH', 'LH_std', 'Tmrca', 'Tmrca_std', 'mu', 'mu_std']
    df = pandas.read_csv(fname, names=columns,header=0)
    df = df[[len(k) > 10 for k in df.File]]
    #import ipdb; ipdb.set_trace()
    df['dTmrca'] = -(df['Sim_Tmrca'] - df['Tmrca'])
    return df

def create_pivot_table(df, T_over_N=None, mean_or_median='median'):
    """
    Create the pivot table to plot from the raw dataframe.
    Args:

     - df (pandas.DataFrame): the raw dataframe as read from a CSV file. Regardless
     of the source data (TreeTime, LSD, or BEAST), dataframe is processed in the
     unified way as soon as it has the following columns:
        - T: (the tot evolution time, or the tree diameter)
        - N: (population size)
        - Nmu: (N*Mu - product of the pop sizez to the mutation rate used in simulations)
        - Sim_mu: mutation rate used in simulations
        - mu: reconstructed mutation rate
        - dTmrca: difference between the real and reconstructed Tmrca values

     - T_over_N(float or None): the total evolution time expressed in the expected
     coalescence times scale. If not None, only those datapoints with correspnditng
     T/N values will be left for the pivot. Otherwise, no filtering is performed.
     By default: the following values are available:
        - 2.
        - 4.
        - 10.
     NOTE: any other values can be produced by re-running the simulations
     (generate_simulated_data_submit.py script) with other parameters

     - mean_or_median(str, possible values: 'mean', 'median'): how errorbars should
     be calculated.
         - 'mean': the datapoint is placed in the mean position, errorbars show
         the standard deviation
         - 'median': datapoint is the median of the distribution, the errorbars are
         quinatiles.
    """

    if T_over_N is not None:
        DF = df[ df["T"] / df["N"] == T_over_N ]
    else:
        DF = df

    N_MUS = np.unique(DF.Nmu)
    N_MUS_idxs = np.ones(N_MUS.shape, dtype=bool)

    mu_mean = []
    mu_err = []
    tmrca_mean = []
    tmrca_err = []

    for idx, N_MU  in enumerate(N_MUS):
        idxs = DF.Nmu == N_MU
        if idxs.sum() == 0:
            N_MUS_idxs[idx] = False
            continue

        dMu = -(DF.Sim_mu[idxs] - DF.mu[idxs])/DF.Sim_mu[idxs]
        dMu.sort_values(inplace=True)
        #dMu = dMu[int(dMu.shape[0]*0.05) : int(dMu.shape[0]*0.95)]

        dTmrca = DF.dTmrca[idxs]/DF.N[idxs]
        dTmrca.sort_values(inplace=True)
        #dTmrca = dTmrca[int(dTmrca.shape[0]*0.05) : int(dTmrca.shape[0]*0.95)]

        if mean_or_median == "mean":
            mu_mean.append(np.mean(dMu))
            mu_err.append(np.std(dMu))

            tmrca_mean.append(np.mean(dTmrca))
            tmrca_err.append(np.std(dTmrca))
        else:
            q75, q25 = np.percentile(dMu, [75 ,25])
            mu_err.append((q75 - q25)) #np.std(DF.dTmrca[idxs])
            mu_mean.append(np.median(dMu))
            q75, q25 = np.percentile(dTmrca, [75 ,25])
            tmrca_err.append((q75 - q25)) #np.std(DF.dTmrca[idxs])
            tmrca_mean.append(np.median(dTmrca))


    res = pandas.DataFrame({
        "Nmu" : N_MUS[N_MUS_idxs],
        "dMu_mean" : mu_mean,
        "dMu_err" : mu_err,
        "dTmrca_mean" : tmrca_mean,
        "dTmrca_err" : tmrca_err,
        })
    res = res.sort_values(by='Nmu')
    return res

def plot_simulated_data(Tmrca_or_Mu,
    treetime_pivot=None, lsd_pivot=None, beast_pivot=None,
    figname=None, plot_idxs=None):
    """
    TODO
    """

    from plot_defaults import shift_point_by_markersize

    fig = plt.figure(figsize=onecolumn_figsize)
    axes = fig.add_subplot(111)

    axes.grid('on')
    axes.set_xscale('log')

    if Tmrca_or_Mu == 'Mu':
        mean = 'dMu_mean'
        err = 'dMu_err'
        title = "Clock rate deviation"
        ylabel = "relative clock rate error, $[\Delta\mu / \mu]$"
        text_overestimated = '$\mathrm{\mu}$ overestimated'
        text_underestimated = '$\mathrm{\mu}$ underestimated'

    elif Tmrca_or_Mu == 'Tmrca':
        mean = 'dTmrca_mean'
        err = 'dTmrca_err'
        title = "Accuracy of Tmrca prediction"
        ylabel = "relative $T_{mrca}$ error, $[\Delta\mathrm{T_{mrca}} / \mathrm{N}]$"
        text_overestimated = '$\mathrm{T_{mrca}}$ too late'
        text_underestimated = '$\mathrm{T_{mrca}}$ too early'

    else:
        raise Exception("Unknown plot type!")

    # Plot treetime
    if treetime_pivot is not None:
        x, y = shift_point_by_markersize(axes, treetime_pivot["Nmu"], treetime_pivot[mean], +markersize*.75)

        if plot_idxs is None:
            tt_plot_idxs = np.ones(x.shape[0] ,dtype=bool)
        else:
            tt_plot_idxs = plot_idxs

        axes.errorbar(x[tt_plot_idxs],
                      y[tt_plot_idxs],
                      (treetime_pivot[err].values/2)[tt_plot_idxs],
            fmt='-',
            marker='o',
            markersize=markersize,
            #markerfacecolor='w',
            markeredgecolor=tt_color,
            mew=1.3,
            c=tt_color, label="TreeTime")

    # Plot BEAST
    if beast_pivot is not None:
        if plot_idxs is None:
            beast_plot_idxs = np.ones(beast_pivot.shape[0] ,dtype=bool)
        else:
            beast_plot_idxs = plot_idxs

        axes.errorbar(beast_pivot["Nmu"].loc[beast_plot_idxs].values,
                      beast_pivot[mean].loc[beast_plot_idxs].values,
                      beast_pivot[err].loc[beast_plot_idxs].values,
            marker='o',
            markersize=markersize,
            c=beast_color,
            label="BEAST")


    # Plot LSD
    if lsd_pivot is not None:
        x, y = shift_point_by_markersize(axes, lsd_pivot["Nmu"], lsd_pivot[mean], +markersize/2)
        if plot_idxs is None:
            lsd_plot_idxs = np.ones(x.shape[0] ,dtype=bool)
        else:
            lsd_plot_idxs = plot_idxs

        axes.errorbar(x[lsd_plot_idxs],
                      y[lsd_plot_idxs],
                      (lsd_pivot[err].values/2)[lsd_plot_idxs],
            fmt='-',
            marker='o',
            markersize=markersize,
            c=lsd_color,
            label="LSD")

    plt.hlines(0, 0, 1)
    axes.legend(loc=1,fontsize=legend_fs)
    #axes.set_title(title)
    axes.set_ylabel(ylabel, fontsize = label_fs)
    axes.set_xlabel('diversity, $\mathrm{N}\cdot\mu$', fontsize = label_fs)
    for label in axes.get_xticklabels():
            label.set_fontsize(tick_fs)
    for label in axes.get_yticklabels():
            label.set_fontsize(tick_fs)

    fig.text(0.15, 0.85, text_overestimated, fontsize=tick_fs)
    fig.text(0.15, 0.15, text_underestimated, fontsize=tick_fs)

    if figname is not None:
        for fmt in formats:
            fig.savefig("{}.{}".format(figname, fmt))


if __name__ == '__main__':

    ##
    ##  Configure the parameters
    ##
    """
    Specify the total evolution time, or the tree diameter (T) relative to the
    coalescence time, as expected from the neutral theory (N). The values of the
    T_over_N  can be varied by re-running the simulations with different evolution
    time or sampling frequencies. By default, the following parameters are available:
     - 2.0
     - 4.0
     - 10.0
    """
    T_over_N = 10.

    """
    What should be used to calculate the error bars and the position of the data
    points.
    Possible values:

     - mean: the point is plotted in the mean of the distribution, the error bars \
     show the standard deviation of the distribution

     - median: the data point is set to the median of the distribution, the error
     bars show the quantiles of the distribution
    """
    mean_or_median = 'median'

    """
    Should save figures? If True, note the figure name in the plot_simulated_data
    function parameters.
    """
    SAVE_FIG = True

    ##
    ##  Set the CSV file names with the data to plot
    ##
    #  files with the reconstruction results:
    treetime_csv = "./simulated_data/_treetime_fasttree_res.csv"
    lsd_csv = "./simulated_data/_lsd_fasttree_res.csv"
    beast_csv = "./simulated_data/_beast_res.csv"

    ##
    ## Read, process and plot the data
    ##
    # read csv's to the pandas dataframes:
    treetime_df = read_treetime_results_csv(treetime_csv)
    lsd_df = read_lsd_results_csv(lsd_csv)
    beast_df = read_beast_results_csv(beast_csv)

    # make pivot tables and filter only the relevant parameters:
    lsd_pivot = create_pivot_table(lsd_df, T_over_N=T_over_N, mean_or_median=mean_or_median)
    beast_pivot = create_pivot_table(beast_df, T_over_N=T_over_N, mean_or_median=mean_or_median)
    treetime_pivot = create_pivot_table(treetime_df, T_over_N=T_over_N, mean_or_median=mean_or_median)

    # plot the data: and save figures if needed:
    # plot Tmrca figure:
    plot_simulated_data('Tmrca', treetime_pivot, lsd_pivot, beast_pivot,
        figname="./figs/simdata_Tmrca_TN{}_{}".format(T_over_N, mean_or_median) if SAVE_FIG else None,
        #plot_idxs=np.array([1,2,4,6,7,9,10])
        )

    # plot Mu figure
    plot_simulated_data('Mu', treetime_pivot, lsd_pivot, beast_pivot,
        figname="./figs/simdata_Mu_TN{}_{}".format(T_over_N, mean_or_median) if SAVE_FIG else None,
        #plot_idxs=np.array([1,2,4,6,7,9,10])
        )

