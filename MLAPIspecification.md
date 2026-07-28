# MATLAB Algorithm API Specification

## Input Requirements

The MATLAB algorithm requires:

* embryo position;
* embryo orientation;
* embryo dimensions;
* embryo state;
* tool starting position;
* destination position;
* workspace limits;
* movement settings.

Example input:

```text
Position: [x, y, z] mm
Orientation: yaw angle in degrees
Destination: [x, y, z] mm
```

## Output

The MATLAB algorithm returns:

* whether the movement was successful;
* final embryo position;
* final embryo state;
* final tool position;
* final tool state;
* number of grasp attempts;
* amount of embryo left in the workspace;
* translational requirements of the task;
* rotation required in degrees;

Example output:

```text
Total embryos:        6
Successfully moved:   6
Failed embryos:       0
Free remaining:       0
Still selected:       0
Still grasped:        0
Total grasp attempts: 12
Successful pickups:   6
Average attempts:     2.00
Success rate:         100.0%

Position information:
Start position:          [15.000, 15.000, 10.000] mm
Final position:          [15.000, 15.000, 10.000] mm
Minimum position:        [1.978, 2.150, 1.100] mm
Maximum position:        [46.000, 15.000, 10.000] mm
XYZ position range:      [44.022, 12.850, 8.900] mm

Distance information:
Total tool distance:     443.902 mm
Minimum movement step:   0.040 mm
Maximum movement step:   1.764 mm
Average movement step:   0.710 mm

Rotation information (roll, pitch, yaw):
Minimum orientation:     [0.00, -0.00, -89.18] deg
Maximum orientation:     [0.00, -0.00, 0.00] deg
Maximum yaw adjustment:  88.74 deg
Average yaw adjustment:  51.34 deg
Orientation range:       [0.00, 0.00, 89.18] deg
Net rotation:            [0.00, 0.00, 0.00] deg
Cumulative rotation:     [0.00, 0.00, 359.40] deg
Total angular motion:    359.40 deg
--------------------------------
```

## Required API Operations

The future interface should support the following operations:

### Initialize

Creates the workspace, tool, embryo data, and movement log.

### Load Embryo Data

Use computer vision to upload embryo data as it is recorded.

### Process All Embryos

Repeats the pick-and-place process until no free embryos remain.

### Get Status

Returns the current tool state, embryo states, and movement progress.

### Get Summary

Returns final movement and simulation statistics.

### Reset

Clears the current simulation and prepares the algorithm for another run.

## Tool Movement Sequence

The tool movement can be summarized as:

1. Start at the home position.
2. Select the nearest free embryo.
3. Move above the embryo.
4. Lower the tool.
5. Grasp the embryo.
6. Lift the embryo.
7. Move above the destination.
8. Lower the embryo.
9. Release the embryo.
10. Repeat for the remaining embryos.

## Communication Protocol

1. The client sends initialization settings.
2. MATLAB initializes the workspace and tool.
3. The client sends embryo detection data.
4. MATLAB validates and stores the embryo data.
5. The client requests all embryos to be processed.
6. MATLAB executes the movement algorithm.
7. MATLAB returns the result.
8. The client requests the final summary.
9. MATLAB returns embryo and movement statistics.

## Data Format

The API exchanges information using JSON.

Positions are expressed in millimetres.

Rotations are expressed in degrees.

Embryo IDs are unique integers.

## Matlab Functions

The future API will call existing MATLAB functions.

| API operation   | MATLAB functions                                           |
| --------------- | ---------------------------------------------------------- |
| Initialize      | `createWorkspace`, `createToolHead`, `initializeMotionLog` |
| Load embryos    | `detectEmbryos`, `createEmbryoFromYOLO`                    |
| Detect clusters | `detectClusteredEmbryos`                                   |
| Select embryo   | `selectNearEmbryo`                                         |
| Move embryo     | movement and grasping functions                            |
| Get summary     | `simulationSummary`                                        |
| Reset           | reinitialize workspace, tool, embryos, and log             |

The embryo movement operation uses:

```text
moveToolToEmbryo
lowerToolToEmbryo
graspEmbryo
liftTool
moveToolFinal
lowerToolToMovedPosition
releaseEmbryo
returnHome
```

## Error Handling

The MATLAB algorithm should return an error when:

* the embryo ID does not exist;
* no free embryos remain;
* the destination is outside the workspace;
* the grasp fails;
* the requested movement is invalid;
* input data are missing.

Example:

```json
{
  "success": false,
  "error": "TARGET_OUTSIDE_WORKSPACE"
}
```

