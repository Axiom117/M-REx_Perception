function [embryos, tool, motionLog] = moveTool( ...
    embryos, tool, targetPosition, targetRotation, ...
    numSteps, workspace, showIDs, showArrows, motionLog)

% Starting translation and rotation
startPosition = tool.pose(1:3, 4);
startRotation = tool.pose(1:3, 1:3);

% Extract starting and target yaw angles    
startYaw = atan2(startRotation(2,1), startRotation(1,1));

if isscalar(targetRotation)
    targetYaw = targetRotation;
elseif isequal(size(targetRotation), [3, 3])
    targetYaw = atan2(targetRotation(2,1), targetRotation(1,1));
else
    error("targetRotation must be a scalar yaw angle or a 3-by-3 rotation matrix.")
end

% Find shortest angular movement
yawDifference = atan2( ...
    sin(targetYaw - startYaw), ...
    cos(targetYaw - startYaw));
    
motionLog.moveYawChanges(end+1,1) = abs(yawDifference);


for k = 1:numSteps

    % stop as soon as a stop was requested from the figure
    if simulationStopped()
        break
    end

    alpha = k / numSteps;

    % Interpolate position

    tool.position = ...
        (1 - alpha) * startPosition + ...
        alpha * targetPosition;

    % Interpolate yaw rotation

    currentYaw = startYaw + alpha * yawDifference;

    tool.orientation = [
        cos(currentYaw), -sin(currentYaw), 0;
        sin(currentYaw),  cos(currentYaw), 0;
        0,                0,               1
    ];

    % Update complete tool pose
    tool.pose = [
        tool.orientation, tool.position;
        0, 0, 0, 1
    ];

    % Make attached embryo follow the tool

    if tool.hasEmbryo

        attachedID = tool.attachedEmbryoID;

        embryos(attachedID).position = ...
            tool.position - [0; 0; tool.clearance];

        % Embryo now rotates with the tool
        embryos(attachedID).orientation = tool.orientation;

        embryos(attachedID).pose = [
            embryos(attachedID).orientation, ...
            embryos(attachedID).position;
            0, 0, 0, 1
        ];
    end

    % Record and display movement

    motionLog = recordToolMotion(motionLog, tool);

    updateSimulation( ...
        workspace, embryos, tool, showIDs, showArrows);

end

tool.targetPosition = targetPosition;

end