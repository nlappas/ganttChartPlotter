# ganttChartPlotter
Simple python script to print gantt charts for single/multitasking machines


## Features:
-  .png/.eps file formats supported. DPI can be set.
-  Multiple orders supported
-  Multiple tasks per machine with independent batch sizes
-  Task overlap detection
-  Automatic identification and consolidation of subtasks for multitasking machines
-  Duplicate task detection
-  Automatic color assignment to unique tasks
-  Legend generation to different file


 ## Sample Input format for a .gantt file
 Columns should be separated with at least one space character.
 Each row entry should begin after a `\n` (newline)

```
   Machine  T_begin   T_end  Operation   Batch_size
+-------------------------------------------- sampleResult.gantt---+
|  PU0_M0_B 0        0.833333 A          40.2                      |
|  PU0_M0_B 1.83333  2.66667  B          80.6                      |
|  PU2_M3_B 0.833333 1.83333  C          32                        |
|  PU2_M3_B 2.83333  3.83333  B          50                        |
+------------------------------------------------------------------+
```

-  For the MTS case, the machine name has to be formatted as:
 ```
 ProcessingUnitName_MachineName_OrderName
 for example PU0_M0_B :
       Processing Unit: PU0
       Machine        : M0
       Order Name     : B
```
-  For the SCH case no restrictions apply.

## Script Execution
 To execute this script `python >= 3.4` is required
 command: `plotGantt.py TYPE path/to/result/file.gantt`
  where `TYPE` is : `MTS / SCH`
