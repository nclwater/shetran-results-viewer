from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os

def _read(in_file):
    table = open(in_file, "r")
    table.readline()
    obs = []
    sim = []
    days = []
    for line in table:
        lineList = line.rstrip().split(",")
        dayVal = lineList[0]
        obsVal = lineList[1]
        simVal = lineList[2]

        obs.append(float(obsVal))

        sim.append(float(simVal))

        days.append(datetime.strptime(dayVal, '%d/%m/%Y'))

    table.close()
    return obs, sim, days


def plot_time_series(in_file, out_dir=None):
    """Creates a plot of observed verses simulated discharge

    Args:
        in_file (str): Path to the input CSV file.
        out_dir (str): Folder to save the output PNG into.

    Returns:
        None

    """

    obs, sim, days = _read(in_file)

    # plot the graph!
    # fig, ax = plt.subplots()
    plt.figure(dpi=300, figsize=[12.0, 5.0])
    plt.subplots_adjust(bottom=0.2)
    plt.plot_date(x=days, y=obs, fmt="b-")
    plt.plot_date(x=days, y=sim, fmt="r-", alpha=0.75)
    plt.gca().set_ylim(bottom=0)
    plt.title("Observed vs simulated flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.grid(True)
    plt.xticks(rotation=70)

    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_hydrograph.png")

    plt.show()



def get_nse(in_file):
    """Calculates the Nash Sutcliffe Efficiency of observed vs simulated discharge.

        Args:
            in_file (str): Path to the input CSV file.

        Returns:
            float: Value of NSE

        """
    obs, sim, days = _read(in_file)

    diffList = []
    obsDiffList = []
    meanObs = np.mean(obs)
    for a in range(len(obs)):
        diffList.append((obs[a] - sim[a]) ** 2)
        obsDiffList.append((obs[a] - meanObs) ** 2)

    return 1 - (sum(diffList) / sum(obsDiffList))


def get_percentiles(in_file, out_dir=None):
    """Calculates percentiles of observed vs simulated discharge at 0, 1, 5-100 in steps of 5 and 99.

            Args:
                in_file (str): Path to the input CSV file.
                out_dir (str,optional): Path to output CSV file.

            Returns:
                tuple: First element is a list of percentiles, second is the observed percentiles
                    and third is the simulated percentiles

    """
    percentiles_list = range(5, 100, 5)
    percentiles_list.append(99)
    percentiles_list.insert(0, 1)

    obs, sim, days = _read(in_file)

    obs_percentiles = []
    sim_percentiles = []
    for perc in percentiles_list:
        obs_percentiles.append(np.percentile(obs, perc))
        sim_percentiles.append(np.percentile(sim, perc))

    if out_dir:

        percentiles_file = open(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_percentiles.csv", "w")
        percentiles_file.write("Percentile,Observed,Simulated\n")
        for x in range(len(percentiles_list)):
            percentiles_file.write(
                str(percentiles_list[x]) + "," + str(obs_percentiles[x]) + "," + str(sim_percentiles[x]) + "\n")
        percentiles_file.close()

    return percentiles_list, obs_percentiles, sim_percentiles




def plot_exceedance(in_file, out_dir=None):
    """Saves an exceedance curve plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """
    percentilesList, obsPercentiles, simPercentiles = get_percentiles(in_file)

    qList = percentilesList
    qList.reverse()
    plt.figure(figsize=[12.0, 5.0], dpi=300)
    plt.plot(qList, obsPercentiles, c="b", ls="-")
    plt.plot(qList, simPercentiles, c="r", ls="-", alpha=0.75)
    plt.title("Flow duration curve of observed vs simulated flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("% Of the time indicated discharge was equalled or exceeded")
    plt.grid(True)
    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_Flow_Duration_Curve.png")

    plt.show()


def plot_water_balance(in_file, out_dir=None):
    """Saves a water balance plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """
    def doWaterBalance(obsOrSim):
        """Calculates the water balance of either the observed or simulated values

        Args:
                in_file (str): Path to the input CSV file.
                obsOrSim (str): Either 'o' (observed) or 's' (simulated).

            Returns:
                A list of monthly means Jan-Dec

        """

        if obsOrSim == "o":
            x = 1
        elif obsOrSim == "s":
            x = 2

        runFile = open(in_file)
        runFile.readline()

        runJanValsList = []
        runFebValsList = []
        runMarValsList = []
        runAprValsList = []
        runMayValsList = []
        runJunValsList = []
        runJulValsList = []
        runAugValsList = []
        runSepValsList = []
        runOctValsList = []
        runNovValsList = []
        runDecValsList = []

        d = datetime(1990, 1, 1)

        for line in runFile:
            if d.month == 1:
                runJanValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 2:
                runFebValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 3:
                runMarValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 4:
                runAprValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 5:
                runMayValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 6:
                runJunValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 7:
                runJulValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 8:
                runAugValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 9:
                runSepValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 10:
                runOctValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 11:
                runNovValsList.append(float(line.rstrip().split(",")[x]))
            if d.month == 12:
                runDecValsList.append(float(line.rstrip().split(",")[x]))

            d = d + timedelta(days=1)

        runFile.close()

        dataList = [np.mean(runJanValsList), np.mean(runFebValsList)
            , np.mean(runMarValsList)
            , np.mean(runAprValsList)
            , np.mean(runMayValsList)
            , np.mean(runJunValsList)
            , np.mean(runJulValsList)
            , np.mean(runAugValsList)
            , np.mean(runSepValsList)
            , np.mean(runOctValsList)
            , np.mean(runNovValsList)
            , np.mean(runDecValsList)]

        return dataList

    obs = doWaterBalance("o")
    sim = doWaterBalance("s")

    months = [i + 1 for i in range(12)]

    plt.figure(dpi=300, figsize=[12.0, 5.0])
    plt.plot(months, obs, c="b", ls="-")
    plt.plot(months, sim, c="r", ls="-", alpha=0.75)
    plt.title("Monthlys Average Flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("Month")
    plt.grid(True)
    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_Monthly_Water_Balance.png")
    plt.show()



# make folder for graphs and outputs
# if not os.path.exists(out_dir):
#     os.mkdir(out_dir)

# NSE = timeSeriesPlotter()

# exceedanceCurve()
# wbGraph()
#
# print "NSE = ", NSE

