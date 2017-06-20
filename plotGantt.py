# Filename: plotGantt.py
#
# Description:
#   Plot Gantt charts for scheduling/multitasking
#   scheduling problems
#
#          Copyright (c) 2017
#             Nikos Lappas
#      Carnegie Mellon University
#

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import math

# Sample Input format for a .gantt file
# Columns should be separated with at least one space character
# Each row entry should begin after a \n (newline)
#
#
# Machine  T_begin   T_end  Operation   Batch_size
#------------------------------------------- sampleResult.gantt---+
# PU0_M0_B 0        0.833333 A          40.2                        |
# PU0_M0_B 1.83333  2.66667  B          80.6                        |
# PU2_M3_B 0.833333 1.83333  C          32                          |
# PU2_M3_B 2.83333  3.83333  B          50                          |
#-------------------------------------------------------------------+
#
#
# For the MTS case, the machine name has to be formatted as:
# ProcessingUnitName_MachineName_OrderName
# for example PU0_M0_B :
#       Processing Unit: PU0
#       Machine        : M0
#       Order Name     : B
#
# For the SCH case no restrictions apply.
#
# To execute this script python >= 3.4 is required
# command: plotGantt.py TYPE path/to/result/file.gantt
#        +--where TYPE is : MTS / SCH


###############################################
# User configuration
MYDEBUG = False
PLOT_LEGENDS = True
LABEL_SIZE = 7
DPI = 300
MARGIN = 0.02
OUTPUT_FILE_EXTENSION = "png"  # "png" / "eps"
################################################


class task:
    """
    Describes a box in a gantt chart
    """
    tBegin = 0
    tEnd = 0
    batchSize = 0
    order = ""
    machine = ""
    processingUnit = ""
    operation = ""
    subtasks = []

    def print(self, padding=""):
        print(padding + "Task: " + self.operation + "\n  |")
        print(padding + "  --- Begins at: " + str(self.tBegin))
        print(padding + "  --- Ends at: " + str(self.tEnd))
        print(padding + "  --- Belongs to Order: " + self.order)
        print(padding + "  --- Processed in Machine: " + self.machine)
        print(padding + "  --- Part of Processing Unit: " + self.processingUnit)
        print(padding + "  --- Batch Size: " + str(self.batchSize))
        if len(self.subtasks) != 0:
            print("    --- Contains the following subTasks: ")
            for sub in self.subtasks:
                sub.print("   ")
            print("-----END OF SUB TASKS ----")


def getMachines(tasks):
    """
    Iterate all tasks in a list of tasks and extract machines
    :param tasks: List of tasks
    :return: Unique Machines Across Tasks
    """
    uniqueMachines = []
    for t in tasks:
        if t.machine not in uniqueMachines:
            uniqueMachines.append(t.machine)
    return uniqueMachines


def getOrders(tasks):
    """
    Iterate all tasks in a list and extract the unique orders
    :param tasks:
    :return: Unique orders across tasks
    """
    uniqueOrders = []
    for t in tasks:
        if t.order not in uniqueOrders:
            uniqueOrders.append(t.order)
    return uniqueOrders


def getProccessingUnits(tasks):
    """
    Iterate all tasks in a list and extract the unique processing units
    :param tasks:
    :return: Unique processing units across tasks
    """
    uniquePUs = []
    for t in tasks:
        if t.processingUnit not in uniquePUs:
            uniquePUs.append(t.processingUnit)
    return uniquePUs


def getOperations(tasks):
    """
    Iterate all tasks in a list and extract the unique processing units
    :param tasks:
    :return: unique operations across tasks
    """
    uniqueOps = []
    for t in tasks:
        if t.operation not in uniqueOps:
            uniqueOps.append(t.operation)
    return uniqueOps


def checkLineStandardCompliance(line):
    """
    Check whether the results file (.gantt) has proper formatting
    :param line: the line from the input file
    :return:
    """
    if len(line) != 5:
        print(line + " HAS WRONG NUMBER OF COLUMNS: " + str(len(line)))
        exit(5)


def checkMTSinfoCompliance(info):
    """
    Check whether the first column of the MTS .gantt file adheres to the standard
    :param info:
    :return:
    """
    if len(info) != 3:
        print("MTS INFO DOES NOT ADHERE TO MY STANDARD: processingUnit_machine_order")
        exit(5)


def parseTasks(mode, fileName):
    """
    parse the .gantt file and create a list of tasks
    :param mode: "MTS" / "SCH"
    :param fileName: the full directory to the .gantt file
    :return: the list of tasks
    """
    allTasks = []
    with open(fileName) as f:
        for line in f:
            words = line.split(" ")
            checkLineStandardCompliance(words)
            thisTask = task()
            thisTask.tBegin = float(words[1])
            thisTask.tEnd = float(words[2])
            thisTask.operation = words[3]
            thisTask.batchSize = float(words[4])
            thisTask.machine = words[0]
            if mode == "MTS":
                mtsInfo = words[0].split("_")
                checkMTSinfoCompliance(mtsInfo)
                thisTask.processingUnit = mtsInfo[0]
                thisTask.machine = mtsInfo[1]
                thisTask.order = mtsInfo[2]
            allTasks.append(thisTask)
    return allTasks


def findTaskInList(task, taskList):
    """
    Search for a task within a task list
    :param task:
    :param taskList:
    :return: true if found, false o/w
    """
    found = False
    for t in taskList:
        if t.tBegin == task.tBegin and t.tEnd == task.tEnd and t.batchSize == task.batchSize \
                and t.order == task.order and t.machine == task.machine and t.processingUnit == task.processingUnit \
                and t.operation == task.operation:
            found = True
            return found
    return found


def removeDuplicateTasks(tasks):
    """
    Remove duplicate tasks from a task list
    :param tasks:
    :return:
    """
    if len(tasks) < 2:
        return tasks
    uniqueTasks = []

    for t in tasks:
        haveSeenT = findTaskInList(t, uniqueTasks)
        if not haveSeenT:
            uniqueTasks.append(t)

    return uniqueTasks


def consolidateSiblingTasks(tasks, machines):
    """
    Check for subtasks that belong to the same main task, and
    consolidate them (MTS only)
    :param tasks:
    :param machines:
    :return: the consolidated task list
    """
    reducedTasks = []
    for m in machines:
        compatibleTasks = []
        for t in tasks:
            if m == t.machine:
                compatibleTasks.append(t)
        slots = []  # time slot
        for ct in compatibleTasks:
            thisSlot = (ct.tBegin, ct.tEnd)
            if thisSlot not in slots:
                slots.append(thisSlot)
        for slot in slots:
            concurrentTasks = []
            for ct in compatibleTasks:
                ctSlot = (ct.tBegin, ct.tEnd)
                if ctSlot == slot:
                    concurrentTasks.append(ct)
            if len(concurrentTasks) > 1:
                mainTask = task()
                mainTask.machine = m
                mainTask.processingUnit = concurrentTasks[0].processingUnit
                mainTask.operation = "MAIN_" + concurrentTasks[0].operation
                (mainTask.tBegin, mainTask.tEnd) = slot
                subs = []
                for cct in concurrentTasks:
                    subs.append(cct)
                    if cct.machine != mainTask.machine  or cct.processingUnit != mainTask.processingUnit \
                        or cct.tBegin != mainTask.tBegin or cct.tEnd != mainTask.tEnd:
                        print("SUBTASKS DO NOT MATCH MAIN TASK")
                        cct.print()
                        print("\n VS \n")
                        mainTask.print()
                        exit(5)
                subs = removeDuplicateTasks(subs)
                if len(subs) == 1:
                    mainTask = subs[0]
                else:
                    mainTask.subtasks = subs
                    totalBatch = 0.0
                    for thisSub in mainTask.subtasks:
                        totalBatch += thisSub.batchSize
                    mainTask.batchSize = totalBatch
                reducedTasks.append(mainTask)
            elif len(concurrentTasks) == 1:
                reducedTasks.append(concurrentTasks[0])
            else:
                print("INVALID NUMBER OF TASKS PER TIME SLOT")
                exit(5)
    return reducedTasks


def checkForOverlappingTasks(tasks, machines):
    """
    Iterate over all tasks, and determine whether overlapps occur
    For MTS call only after consolidateSiblingTasks has been called
    :param tasks: task list
    :param machines: machine name list
    :return: True if overlap found
    """
    for m in machines:
        compatibleTasks = []
        for t in tasks:
            if m == t.machine:
                compatibleTasks.append(t)
        slots = []  # time slot
        for ct in compatibleTasks:
            thisSlot = (ct.tBegin, ct.tEnd)
            if thisSlot not in slots:
                slots.append(thisSlot)
                # print(thisSlot)
        slots = sorted(slots)
        for s, slt in enumerate(slots[:-1]):
            for slt2 in slots[s+1:]:
                if slt[1] > slt2[0]:
                    print(slt)
                    print(slt2)
                    return True
    return False


def getMakeSpan(tasks):
    """
    get the maximum ending time of all tasks
    :param tasks:
    :return: ms
    """
    ms = 0
    for t in tasks:
        if t.tEnd > ms:
            ms = t.tEnd
    return ms


def makeGanttChart(mode, fileName):
    """
    The main function responsible for parsing the input file,
    building the list of tasks and plotting them via the
    matplotlib facility
    :param mode: "MTS" / "SCH"
    :param fileName: the directory of the .gantt file
    :return: nothing.
    """

    figType = OUTPUT_FILE_EXTENSION  # "png", "eps"

    # extract the figure name and target directory (to store the figures)
    figureFileName = fileName[0:-6]
    k = figureFileName.rfind("/") + 1
    figureFileName = figureFileName[k:]
    k = fileName.rfind("/") + 1
    targetDirectory = ""
    if k == 0:
        targetDirectory = "./"
    else:
        targetDirectory = fileName[0:k]
    targetFname = targetDirectory + figureFileName + "." + figType

    # import the tasks
    tasks = parseTasks(mode, fileName)
    machines = sorted(getMachines(tasks))
    orders = sorted(getOrders(tasks))
    processingUnits = sorted(getProccessingUnits(tasks))
    operations = sorted(getOperations(tasks))

    if mode == "MTS":
        tasks = consolidateSiblingTasks(tasks, machines)
    tasks = removeDuplicateTasks(tasks)
    if checkForOverlappingTasks(tasks, machines):
        print("ERROR! Found overlapping tasks, check your input file!")
        exit(5)

    # Print all of the read tasks in DEBUG mode
    if MYDEBUG:
        for t in tasks:
            t.print()

    # build the figure
    fig = plt.figure(figsize=(10, 5), dpi=DPI)  #  <------      USER OPTION HERE    -----------------
    ax = fig.add_subplot(111)
    ax.set_title(figureFileName)

    # set up the axes
    y_pos = np.arange(len(machines))
    ax.set_yticks(y_pos)
    ax.set_ylim(min(y_pos) - 0.7, max(y_pos) + 0.7)
    ax.set_yticklabels(machines)
    ax.set_xlabel("Time (Hours)")
    x_pos = np.arange(math.ceil(getMakeSpan(tasks))+1)
    ax.set_xticks(x_pos)
    ax.set_axisbelow(True)
    ax.grid(b=True, which="major", axis="x", alpha=0.5)

    # assign a unique color to each order and each operation
    #  http://matplotlib.org/examples/color/colormaps_reference.html
    cmapOrders = plt.cm.Pastel2(np.linspace(0, 1, len(orders)))
    cmapOperations = plt.cm.Pastel2(np.linspace(0, 1, len(operations)))

    # plot the task rectangles
    #  https://stackoverflow.com/questions/21397549/stack-bar-plot-in-matplotlib-and-add-label-to-each-section-and-suggestions
    for i, m in enumerate(machines):
        compatibleTasks = []
        for t in tasks:
            if m == t.machine:
                compatibleTasks.append(t)
        slots = []  # time slots for machine m
        for ct in compatibleTasks:
            for ct in compatibleTasks:
                thisSlot = (ct.tBegin, ct.tEnd)
                if thisSlot not in slots:
                    slots.append(thisSlot)
        slots = sorted(slots)
        if mode == "SCH":
            for s, slt in enumerate(slots):
                thisBatchSize = ""
                thisOperation = ""
                for ct in compatibleTasks:
                    if (ct.tBegin, ct.tEnd) == slt:
                        thisBatchSize = ct.batchSize
                        thisOperation = ct.operation
                thisColor = cmapOperations[operations.index(thisOperation)]
                h = ax.barh(i, width=slots[s][1]-slots[s][0], left=slots[s][0], align='center', color=thisColor)
                bl = h[0].get_xy()
                x = 0.5*h[0].get_width() + bl[0]
                y = 0.5*h[0].get_height() + bl[1]
                ax.text(x, y, str(thisBatchSize), ha='center',va='center')
        elif mode == "MTS":
            for s, slt in enumerate(slots):
                # Get the MAIN task corresponding to the current time slot
                currentTask = 0
                for ct in compatibleTasks:
                    if (ct.tBegin, ct.tEnd) == slt:
                        currentTask = ct
                # Plot the unique task
                if len(currentTask.subtasks) == 0:
                    duration = slots[s][1]-slots[s][0]
                    thisColor = cmapOrders[orders.index(currentTask.order)]

                    h = []
                    h.append(ax.barh(i, width=duration, left=slots[s][0], align='center', color="grey", alpha=0.7))
                    h.append(ax.barh(i, width=duration - 2*MARGIN, left=slots[s][0] + MARGIN, align='center',
                                     color=thisColor, height=0.65, linewidth=0))
                    bl = h[0][0].get_xy()
                    x = 0.5*h[0][0].get_width() + bl[0]
                    y = 0.5*h[0][0].get_height() + bl[1]
                    thisBatchSize = currentTask.batchSize
                    ax.text(x, y, str(thisBatchSize), ha='center',va='center', size=LABEL_SIZE)
                else:
                    # Plot first the MAIN task
                    duration = slots[s][1]-slots[s][0]
                    barHandles = []
                    barHandles.append(ax.barh(i, width=duration, left=slots[s][0],
                                              align='center', color="grey", alpha=0.7))
                    bl = barHandles[0][0].get_xy()
                    l = slots[s][0] + MARGIN
                    # Plot the SUB tasks
                    for counter, thisSub in enumerate(currentTask.subtasks):
                        thisColor = cmapOrders[orders.index(thisSub.order)]
                        partialDuration = (thisSub.batchSize/currentTask.batchSize) * duration - \
                                          2*MARGIN/len(currentTask.subtasks)
                        barHandles.append(ax.barh(i, width=partialDuration, left=l, align='center', height=0.65, linewidth=0,
                                                  color=thisColor))
                        bl = barHandles[-1][0].get_xy()
                        x = 0.5*barHandles[-1][0].get_width() + bl[0]
                        y = 0.5*barHandles[-1][0].get_height() + bl[1]
                        thisBatchSize = thisSub.batchSize
                        ax.text(x, y, str(thisBatchSize), ha='center',va='center', size=LABEL_SIZE)
                        l = l + partialDuration
        else:
            print("INVALID MODE")
            exit(5)

    # Show / print the figure
    fig.savefig(targetFname, dpi=DPI)
    # if MYDEBUG:
    #     plt.show()
    plt.clf()
    plt.close()


    # plot a legend (print in different file)
    if PLOT_LEGENDS:
        if mode == "SCH":
            pat = []
            leg = plt.figure(figsize=(5, 5), dpi=DPI)
            frame = plt.gca()
            frame.axes.get_xaxis().set_visible(False)
            frame.axes.get_yaxis().set_visible(False)
            leg.patch.set_visible(False)
            for op in operations:
                thisColor = cmapOperations[operations.index(op)]
                pat.append(mpatches.Patch(color=thisColor, label=op))
            plt.legend(handles=pat)
            leg.savefig(targetDirectory + figureFileName + "_legend." + figType, dpi=DPI)
        elif mode == "MTS":
            pat = []
            leg = plt.figure(figsize=(5, 5), dpi= DPI)
            frame = plt.gca()
            frame.axes.get_xaxis().set_visible(False)
            frame.axes.get_yaxis().set_visible(False)
            leg.patch.set_visible(False)
            for ord in orders:
                thisColor = cmapOrders[orders.index(ord)]
                pat.append(mpatches.Patch(color=thisColor, label=ord))
            plt.legend(handles=pat)
            leg.savefig(targetDirectory + figureFileName + "_legend." + figType, dpi=DPI)
        else:
            print("INVALID MODE")
            exit(5)



#######################################################################################################################



def readArgs():
    """
    Reading the command line arguments and performing basic checks
    :return: the list of arguments
    """
    args = sys.argv
    if len(args) != 3:
        print("ERROR - Wrong number of arguments! \n")
        print("Usage: plotGantt.py TYPE path/to/result/file.gantt \n where TYPE is : MTS / SCH")
        exit(5)
    if args[1] != "MTS" and args[1] != "SCH":
        print("ERROR - Wrong type specified! : " + args[1])
        print("Usage: plotGantt.py TYPE path/to/result/file.gantt \n where TYPE is : MTS / SCH")
    return args

if __name__ == "__main__":
    args = readArgs()
    makeGanttChart(args[1], args[2])

