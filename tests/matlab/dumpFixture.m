% dumpFixture.m - MATLAB-side parity trace for the M2 acceptance checks.
%
% Reads tests/fixtures/scenario_basic.json, runs the frozen reference code in
% src/** (read-only) and writes tests/matlab/trace_m2.json for
% tests/test_parity.py (tolerance 1e-9, see migration plan section 9).
%
% Usage (from the project root):
%   /Applications/MATLAB_R2026a.app/bin/matlab -batch "cd tests/matlab; dumpFixture"
%
% Headless notes:
% - updateSimulation.m in this folder shadows the renderer with a no-op that
%   can also record per-step snapshots (follow case). No src file is modified.
% - Grasp outcomes are made deterministic by choosing seeds whose rand() draws
%   satisfy the wanted success/failure pattern; seeds and raw draw values are
%   exported so the Python side can replay the exact outcome sequence.

thisFolder = fileparts(mfilename("fullpath"));
projectFolder = fileparts(fileparts(thisFolder));

addpath(genpath(fullfile(projectFolder, "src")));
addpath(thisFolder);   % shadow renderer (added last -> first on path)

setappdata(0, "TaskFlowStopSimulation", false);
rng(42);

trace = struct();
trace.meta = struct();
trace.meta.matlabVersion = version();
trace.meta.rngSeed = 42;
trace.meta.generatedBy = "tests/matlab/dumpFixture.m";

workspace = createWorkspace("default");
fixturePath = fullfile(projectFolder, "tests", "fixtures", "scenario_basic.json");
fixture = jsondecode(fileread(fixturePath));

hwSim = struct("isSimulation", true, "pump", []);

% ===== A. single moveTool trajectory (50 steps) =============================
toolA = createToolHead(workspace);
startPositionA = toolA.position;
targetPositionA = [25; 17.5; 10];
targetYawA = 0.5;
logA = initializeMotionLog();

[~, toolA, logA] = moveTool( ...
    buildEmbryos(fixture), toolA, targetPositionA, targetYawA, 50, ...
    workspace, false, false, logA);

trace.trajectory = struct();
trace.trajectory.startPosition = startPositionA';
trace.trajectory.targetPosition = targetPositionA';
trace.trajectory.targetYawRad = targetYawA;
trace.trajectory.numSteps = 50;
trace.trajectory.positions = logA.positions;
trace.trajectory.rotation = logA.rotation;
trace.trajectory.toolState = logA.toolState;
trace.trajectory.moveYawChanges = logA.moveYawChanges;
trace.trajectory.finalTargetPosition = toolA.targetPosition';

% ===== B. shortest-angle yaw across +/-pi ===================================
toolB = createToolHead(workspace);
yaw0B = deg2rad(170);
toolB.orientation = [ ...
    cos(yaw0B) -sin(yaw0B) 0; ...
    sin(yaw0B)  cos(yaw0B) 0; ...
    0           0          1];
toolB.pose = [toolB.orientation toolB.position; 0 0 0 1];
targetYawB = deg2rad(-170);
logB = initializeMotionLog();

[~, toolB, logB] = moveTool( ...
    buildEmbryos(fixture), toolB, toolB.position, targetYawB, 20, ...
    workspace, false, false, logB);

trace.wrapCase = struct();
trace.wrapCase.startYawRad = yaw0B;
trace.wrapCase.targetYawRad = targetYawB;
trace.wrapCase.numSteps = 20;
trace.wrapCase.rotation = logB.rotation;
trace.wrapCase.moveYawChanges = logB.moveYawChanges;

% ===== C. attached embryo follows every step ================================
global MREX_TRACE_REC
MREX_TRACE_REC = struct( ...
    "active", false, ...
    "toolPositions", [], "toolOrientations", [], ...
    "attachedPositions", [], "attachedOrientations", []);

toolC = createToolHead(workspace);
toolC.position = [5; 5; 2];
yawC = 0.9;
toolC.orientation = [ ...
    cos(yawC) -sin(yawC) 0; ...
    sin(yawC)  cos(yawC) 0; ...
    0         0         1];
toolC.pose = [toolC.orientation toolC.position; 0 0 0 1];
toolC.hasEmbryo = true;
toolC.attachedEmbryoID = 1;

embryosC = buildEmbryos(fixture);
embryosC(1).position = [5; 5; 0.1];
embryosC(1).orientation = toolC.orientation;
embryosC(1).pose = [embryosC(1).orientation embryosC(1).position; 0 0 0 1];

targetPositionC = [7; 8; 2];
logC = initializeMotionLog();

MREX_TRACE_REC.active = true;
[embryosC, toolC, logC] = moveTool( ...
    embryosC, toolC, targetPositionC, 0.4, 40, ...
    workspace, false, false, logC);
MREX_TRACE_REC.active = false;

trace.followCase = struct();
trace.followCase.numSteps = 40;
trace.followCase.startPosition = [5; 5; 2]';
trace.followCase.startYawRad = yawC;
trace.followCase.targetPosition = targetPositionC';
trace.followCase.targetYawRad = 0.4;
trace.followCase.toolPositions = MREX_TRACE_REC.toolPositions;
trace.followCase.toolOrientations = MREX_TRACE_REC.toolOrientations;
trace.followCase.attachedPositions = MREX_TRACE_REC.attachedPositions;
trace.followCase.attachedOrientations = MREX_TRACE_REC.attachedOrientations;
trace.followCase.finalEmbryoPosition = embryosC(1).position';
trace.followCase.finalEmbryoOrientation = reshape(embryosC(1).orientation, 1, 9);

% ===== D. getMovedPosition grid cases and errors ============================
gridEmbryos = populateEmbryos(workspace, 50);
for i = 1:numel(gridEmbryos)
    gridEmbryos(i).state = "free";
end

movedCases = struct("movedCount", {}, "position", {});
movedCounts = [0 1 49 50];
for k = 1:numel(movedCounts)
    c = movedCounts(k);
    ge = gridEmbryos;
    for i = 1:c
        ge(i).state = "moved";
    end
    pos = getMovedPosition(ge, workspace);
    movedCases(end + 1) = struct("movedCount", c, "position", pos');
end

errorCases = struct("region", {}, "movedCount", {}, "message", {});
wsSmall = workspace;
wsSmall.movedregion = [80 5 4 3];
ge2 = gridEmbryos;
ge2(1).state = "moved";
ge2(2).state = "moved";
errorCases(end + 1) = captureGridError(ge2, wsSmall, 2);

wsDegenerate = workspace;
wsDegenerate.movedregion = [80 5 1 3];
errorCases(end + 1) = captureGridError(gridEmbryos, wsDegenerate, 0);
ge3 = gridEmbryos;
ge3(1).state = "moved";
ge3(2).state = "moved";
errorCases(end + 1) = captureGridError(ge3, wsDegenerate, 2);

trace.movedGrid = struct();
trace.movedGrid.cases = movedCases;
trace.movedGrid.errors = errorCases;

% ===== E. grasp outcomes (forced via seeded draws) and release ==============
[seedSuccess, drawsSuccess] = huntSeed(@(d) d(1) < 0.65, 1);
embryosE = buildEmbryos(fixture);
embryosE(1).state = "selected";
toolE = createToolHead(workspace);
rng(seedSuccess);
[embryosE, toolE] = graspEmbryo(embryosE, toolE, hwSim);

trace.graspSuccess = struct();
trace.graspSuccess.seed = seedSuccess;
trace.graspSuccess.draws = drawsSuccess';
trace.graspSuccess.attempts = embryosE(1).attempts;
trace.graspSuccess.embryoState = string(embryosE(1).state);
trace.graspSuccess.pickedSuccessfully = logical(embryosE(1).pickedSuccessfully);
trace.graspSuccess.toolState = string(toolE.state);
trace.graspSuccess.toolHasEmbryo = logical(toolE.hasEmbryo);
trace.graspSuccess.toolAttachedID = toolE.attachedEmbryoID;

[seedFailOne, drawsFailOne] = huntSeed(@(d) d(1) >= 0.65, 1);
embryosE2 = buildEmbryos(fixture);
embryosE2(1).state = "selected";
toolE2 = createToolHead(workspace);
rng(seedFailOne);
[embryosE2, toolE2] = graspEmbryo(embryosE2, toolE2, hwSim);

trace.graspFailOne = struct();
trace.graspFailOne.seed = seedFailOne;
trace.graspFailOne.draws = drawsFailOne';
trace.graspFailOne.attempts = embryosE2(1).attempts;
trace.graspFailOne.embryoState = string(embryosE2(1).state);
trace.graspFailOne.toolState = string(toolE2.state);
trace.graspFailOne.toolHasEmbryo = logical(toolE2.hasEmbryo);
trace.graspFailOne.toolAttachedID = toolE2.attachedEmbryoID;

[seedFailThree, drawsFailThree] = huntSeed( ...
    @(d) d(1) >= 0.65 && d(2) >= 0.60 && d(3) >= 0.55, 3);
embryosE3 = buildEmbryos(fixture);
embryosE3(1).state = "selected";
toolE3 = createToolHead(workspace);
rng(seedFailThree);
attemptsOut = zeros(1, 3);
embryoStatesOut = strings(1, 3);
toolStatesOut = strings(1, 3);
for k = 1:3
    % graspEmbryo sends a failed embryo back to "free"; the main loop
    % re-selects before every attempt, so mirror that here.
    embryosE3(1).state = "selected";
    [embryosE3, toolE3] = graspEmbryo(embryosE3, toolE3, hwSim);
    attemptsOut(k) = embryosE3(1).attempts;
    embryoStatesOut(k) = string(embryosE3(1).state);
    toolStatesOut(k) = string(toolE3.state);
end

trace.graspFailThree = struct();
trace.graspFailThree.seed = seedFailThree;
trace.graspFailThree.draws = drawsFailThree';
trace.graspFailThree.attempts = attemptsOut;
trace.graspFailThree.embryoStates = embryoStatesOut;
trace.graspFailThree.toolStates = toolStatesOut;
trace.graspFailThree.finalEmbryoState = string(embryosE3(1).state);

movedPositionR = [81; 6; 0.1];
[embryosE, toolE] = releaseEmbryo(embryosE, toolE, hwSim, movedPositionR);

trace.release = struct();
trace.release.movedPosition = movedPositionR';
trace.release.embryoState = string(embryosE(1).state);
trace.release.embryoPosition = embryosE(1).position';
trace.release.embryoOrientation = reshape(embryosE(1).orientation, 1, 9);
trace.release.toolState = string(toolE.state);
trace.release.toolHasEmbryo = logical(toolE.hasEmbryo);
trace.release.toolAttachedID = toolE.attachedEmbryoID;

% ===== F. full engine loop on the fixture (runSimulation.m logic) ===========
rng(42);
embryosL = detectClusteredEmbryos(buildEmbryos(fixture));
toolL = createToolHead(workspace);
logL = initializeMotionLog();
logL = recordToolMotion(logL, toolL);

numStepsF = 50;
targetPoint = [50; 50; 0.1];
iterations = struct( ...
    "iteration", {}, "selectedID", {}, "graspSeed", {}, "graspDraw", {}, ...
    "graspSucceeded", {}, "attemptsAfter", {}, "embryoStatesAfter", {}, ...
    "movedPosition", {}, "toolStateAfter", {});
iterationIndex = 0;

while hasFreeEmbryos(embryosL) && ~simulationStopped()

    iterationIndex = iterationIndex + 1;

    embryosL = selectNearEmbryo(embryosL, targetPoint);
    selectedID = find([embryosL.state] == "selected", 1);

    [embryosL, toolL, logL] = moveToolToEmbryo( ...
        embryosL, toolL, numStepsF, workspace, false, false, logL);

    graspSeed = iterationIndex * 1000 + 7;
    rng(graspSeed);
    graspDraw = rand;
    rng(graspSeed);

    [embryosL, toolL] = graspEmbryo(embryosL, toolL, hwSim);
    logL = recordToolMotion(logL, toolL);
    graspSucceeded = toolL.hasEmbryo;

    movedPosition = [];
    if graspSucceeded
        movedPosition = getMovedPosition(embryosL, workspace);
        [embryosL, toolL, logL] = moveToolFinal( ...
            embryosL, toolL, numStepsF, movedPosition, workspace, false, false, logL);
        [embryosL, toolL] = releaseEmbryo(embryosL, toolL, hwSim, movedPosition);
        logL = recordToolMotion(logL, toolL);
    else
        [embryosL, toolL, logL] = raiseTool( ...
            embryosL, toolL, numStepsF, workspace, false, false, logL);
    end

    rec = struct();
    rec.iteration = iterationIndex;
    rec.selectedID = selectedID;
    rec.graspSeed = graspSeed;
    rec.graspDraw = graspDraw;
    rec.graspSucceeded = logical(graspSucceeded);
    rec.attemptsAfter = [embryosL.attempts];
    rec.embryoStatesAfter = string({embryosL.state});
    rec.movedPosition = movedPosition';
    rec.toolStateAfter = string(toolL.state);
    iterations(iterationIndex) = rec;

end

[embryosL, toolL, logL] = returnHome( ...
    embryosL, toolL, numStepsF, workspace, false, false, logL);

finalPositions = zeros(numel(embryosL), 3);
finalOrientations = zeros(numel(embryosL), 9);
for i = 1:numel(embryosL)
    finalPositions(i, :) = embryosL(i).position';
    finalOrientations(i, :) = reshape(embryosL(i).orientation, 1, 9);
end

trace.engineLoop = struct();
trace.engineLoop.iterations = iterations;
trace.engineLoop.motionLog = logL;
trace.engineLoop.finalEmbryos = struct( ...
    "states", string({embryosL.state}), ...
    "attempts", [embryosL.attempts], ...
    "pickedSuccessfully", logical([embryosL.pickedSuccessfully]), ...
    "positions", finalPositions, ...
    "orientations", finalOrientations);
trace.engineLoop.finalTool = struct( ...
    "position", toolL.position', ...
    "orientation", reshape(toolL.orientation, 1, 9), ...
    "state", string(toolL.state), ...
    "hasEmbryo", logical(toolL.hasEmbryo));
trace.engineLoop.summary = summaryStats(embryosL, logL);
trace.engineLoop.summaryText = evalc("simulationSummary(embryosL, logL)");

% ===== write trace ==========================================================
outFile = fullfile(thisFolder, "trace_m2.json");
fid = fopen(outFile, "w");
if fid < 0
    error("dumpFixture: cannot open output file: " + outFile);
end
fwrite(fid, jsonencode(trace), "char");
fclose(fid);

disp("trace written: " + outFile);

% ===== local functions ======================================================
function embryos = buildEmbryos(fixture)

embryos = struct([]);
for i = 1:numel(fixture.embryos)
    e0 = fixture.embryos(i);
    e = struct();
    e.state = string(e0.state);
    e.attempts = e0.attempts;
    e.pickedSuccessfully = logical(e0.picked_successfully);
    e.shape = 'ellipsoid';
    e.width = e0.width;
    e.length = e0.length;
    e.height = e0.height;
    e.confidence = e0.confidence;
    e.position = e0.position(:);
    yaw = e0.yaw;
    e.orientation = [ ...
        cos(yaw) -sin(yaw) 0; ...
        sin(yaw)  cos(yaw) 0; ...
        0        0         1];
    e.pose = [e.orientation e.position; 0 0 0 1];
    e.isClustered = false;
    if i == 1
        embryos = e;
    else
        embryos(i) = e;
    end
end

end

function errRec = captureGridError(embryos, ws, movedCount)

errRec = struct("region", ws.movedregion, "movedCount", movedCount, "message", "");
try
    getMovedPosition(embryos, ws);
catch ME
    errRec.message = string(ME.message);
end
if errRec.message == ""
    error("dumpFixture: getMovedPosition did not raise (movedCount=%d)", movedCount);
end

end

function [seed, draws] = huntSeed(predicate, numDraws)

seed = -1;
draws = [];
for cand = 1:200000
    rng(cand);
    d = rand(numDraws, 1);
    if predicate(d)
        seed = cand;
        draws = d;
        return
    end
end
error("dumpFixture: no seed found for the requested draw pattern");

end

function stats = summaryStats(embryos, motionLog)
% Numeric mirror of simulationSummary.m (frozen) with snake_case JSON field
% names identical to SummaryReport.to_dict() on the Python side.

states = string({embryos.state});

stats = struct();
stats.total = numel(embryos);
stats.moved = sum(states == "moved");
stats.grasped = sum(states == "grasped");
stats.selected = sum(states == "selected");
stats.failed = sum(states == "failed");
stats.free = sum(states == "free");
stats.total_attempts = sum([embryos.attempts]);
stats.successful_pickups = sum([embryos.pickedSuccessfully]);
stats.average_attempts = 0;
if stats.total > 0
    stats.average_attempts = stats.total_attempts / stats.total;
end
stats.success_rate = 0;
if (stats.moved + stats.failed) > 0
    stats.success_rate = 100 * stats.moved / (stats.moved + stats.failed);
end

stats.num_motion_samples = size(motionLog.positions, 1);
stats.total_tool_distance = 0;
stats.minimum_segment_distance = 0;
stats.maximum_segment_distance = 0;
stats.average_segment_distance = 0;
if stats.num_motion_samples >= 2
    positionDifferences = diff(motionLog.positions, 1, 1);
    segmentDistances = vecnorm(positionDifferences, 2, 2);
    movingSegments = segmentDistances(segmentDistances > 1e-9);
    stats.total_tool_distance = sum(segmentDistances);
    if ~isempty(movingSegments)
        stats.minimum_segment_distance = min(movingSegments);
        stats.maximum_segment_distance = max(movingSegments);
        stats.average_segment_distance = mean(movingSegments);
    end
end

if stats.num_motion_samples > 0
    stats.start_position = motionLog.positions(1, :);
    stats.final_position = motionLog.positions(end, :);
    stats.minimum_position = min(motionLog.positions, [], 1);
    stats.maximum_position = max(motionLog.positions, [], 1);
    stats.position_range = stats.maximum_position - stats.minimum_position;
else
    stats.start_position = [0 0 0];
    stats.final_position = [0 0 0];
    stats.minimum_position = [0 0 0];
    stats.maximum_position = [0 0 0];
    stats.position_range = [0 0 0];
end

stats.num_rotation_samples = size(motionLog.rotation, 1);
if stats.num_rotation_samples >= 2
    unwrappedRotation = unwrap(motionLog.rotation, [], 1);
    rotationDifferences = diff(unwrappedRotation, 1, 1);

    movingYawChanges = motionLog.moveYawChanges(motionLog.moveYawChanges > 1e-9);
    if ~isempty(movingYawChanges)
        stats.maximum_yaw_adjustment = max(movingYawChanges);
        stats.average_yaw_adjustment = mean(movingYawChanges);
    else
        stats.maximum_yaw_adjustment = 0;
        stats.average_yaw_adjustment = 0;
    end

    stats.cumulative_rotation = sum(abs(rotationDifferences), 1);
    stats.net_rotation = unwrappedRotation(end, :) - unwrappedRotation(1, :);
    stats.minimum_rotation = min(unwrappedRotation, [], 1);
    stats.maximum_rotation = max(unwrappedRotation, [], 1);
    stats.rotation_range = stats.maximum_rotation - stats.minimum_rotation;
    stats.total_angular_motion = sum(vecnorm(rotationDifferences, 2, 2));
elseif stats.num_rotation_samples == 1
    stats.maximum_yaw_adjustment = 0;
    stats.average_yaw_adjustment = 0;
    stats.cumulative_rotation = [0 0 0];
    stats.net_rotation = [0 0 0];
    stats.minimum_rotation = motionLog.rotation(1, :);
    stats.maximum_rotation = motionLog.rotation(1, :);
    stats.rotation_range = [0 0 0];
    stats.total_angular_motion = 0;
else
    stats.maximum_yaw_adjustment = 0;
    stats.average_yaw_adjustment = 0;
    stats.cumulative_rotation = [0 0 0];
    stats.net_rotation = [0 0 0];
    stats.minimum_rotation = [0 0 0];
    stats.maximum_rotation = [0 0 0];
    stats.rotation_range = [0 0 0];
    stats.total_angular_motion = 0;
end

stats.minimum_rotation_deg = rad2deg(stats.minimum_rotation);
stats.maximum_rotation_deg = rad2deg(stats.maximum_rotation);
stats.rotation_range_deg = rad2deg(stats.rotation_range);
stats.net_rotation_deg = rad2deg(stats.net_rotation);
stats.cumulative_rotation_deg = rad2deg(stats.cumulative_rotation);
stats.total_angular_motion_deg = rad2deg(stats.total_angular_motion);
stats.maximum_yaw_adjustment_deg = rad2deg(stats.maximum_yaw_adjustment);
stats.average_yaw_adjustment_deg = rad2deg(stats.average_yaw_adjustment);

end
