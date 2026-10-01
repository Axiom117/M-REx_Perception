clear
clc
close all

% clear any stop request left over from a previous run
setappdata(0, "TaskFlowStopSimulation", false);

projectFolder = fileparts(mfilename("fullpath"));

addpath(genpath(fullfile(projectFolder,"src")));

% Mode
mode = "simulation";
% mode = "actual";

% Workspace config: name of a YAML config file in the config/workspace folder
workspaceConfig = "default";

% create workspace for simulation
workspace = createWorkspace(workspaceConfig);

% initialize pump and hardware
hardware = struct();

switch mode

    case "simulation"

        hardware.isSimulation = true;
        hardware.pump = [];

    case "actual"

        hardware.isSimulation = false;

        pump = serialport("COM3",115200);

        configureTerminator(pump,"CR");
        pump.Timeout = 3;
        flush(pump);

        % Pump configuration
        writeline(pump,"diameter 15.9 mm");
        writeline(pump,"irate 20 ml/min");
        writeline(pump,"wrate 20 ml/min");

        hardware.pump = pump;

    otherwise

        error("Unknown mode.")

end

% Embryo source: "random" populates randomly arranged embryos,
% "image" detects embryos from a picture with YOLO
embryoSource = "random";
% embryoSource = "image";
numRandomEmbryos = 6;

% create path to python code and extract position
imagePath = fullfile(projectFolder, "images", "sample.jpg");

numSteps = 50;
showIDs = false;
showArrows = false;
targetPoint = [50; 50; 0.1];

switch embryoSource

    case "image"

        embryos = detectEmbryos(imagePath, workspace);

    case "random"

        embryos = populateEmbryos(workspace, numRandomEmbryos);

    otherwise

        error("Unknown embryo source.")

end

embryos = detectClusteredEmbryos(embryos);

toolhead = createToolHead(workspace);

motionLog = initializeMotionLog();
motionLog = recordToolMotion(motionLog, toolhead);

figure

updateSimulation( ...
    workspace, embryos, toolhead, showIDs, showArrows, ...
    "Initial workspace")

% run simulation

while hasFreeEmbryos(embryos) && ~simulationStopped()

    embryos = selectNearEmbryo(embryos, targetPoint);

    [embryos, toolhead, motionLog] = ...
        moveToolToEmbryo( ...
            embryos, ...
            toolhead, ...
            numSteps, ...
            workspace, ...
            showIDs, ...
            showArrows, ...
            motionLog);

    updateSimulation( ...
        workspace, embryos, toolhead, showIDs, showArrows, ...
        "Tool above selected embryo", 0.2)

    [embryos, toolhead] = ...
        graspEmbryo(embryos, toolhead, hardware);

    motionLog = recordToolMotion( ...
        motionLog, toolhead);

    if ~toolhead.hasEmbryo

        [embryos, toolhead, motionLog] = ...
            raiseTool( ...
                embryos, ...
                toolhead, ...
                numSteps, ...
                workspace, ...
                showIDs, ...
                showArrows, ...
                motionLog);

        continue
    end

    updateSimulation( ...
        workspace, embryos, toolhead, showIDs, showArrows, ...
        "Embryo grasped", 0.2)

    movedPosition = ...
        getMovedPosition(embryos, workspace);

    [embryos, toolhead, motionLog] = ...
        moveToolFinal( ...
            embryos, ...
            toolhead, ...
            numSteps,...
            movedPosition, ...
            workspace, ...
            showIDs, ...
            showArrows, ...
            motionLog);

    updateSimulation( ...
        workspace, embryos, toolhead, showIDs, showArrows, ...
        "Tool above moved position", 0.2)

    [embryos, toolhead] = ...
        releaseEmbryo( ...
            embryos, toolhead, hardware, movedPosition);

    motionLog = recordToolMotion( ...
        motionLog, toolhead);

    updateSimulation( ...
        workspace, embryos, toolhead, showIDs, showArrows, ...
        "Embryo released", 0.2)

end

% stop without returning home or reporting when requested
if simulationStopped()
    disp("Simulation stopped before completion.")
    return
end

[embryos, toolhead, motionLog] = ...
    returnHome( ...
        embryos, ...
        toolhead, ...
        numSteps, ...
        workspace, ...
        showIDs, ...
        showArrows, ...
        motionLog);

% create simulation summary

simulationSummary(embryos, motionLog);