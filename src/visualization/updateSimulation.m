% Function for updating the simulation figure with the current state.
% An optional title and pause duration can be given for the phase frames.
% Returns immediately when a stop was requested.
function updateSimulation(workspace, embryos, tool, showIDs, showArrows, frameTitle, pauseDuration)

if simulationStopped()
    return
end

clf

plotEmbryos3D(workspace, embryos, showIDs, showArrows)

hold on

plotToolHead3D(tool)

% keep the stop button and the close behavior across clf
addStopControls(gcf)

if nargin >= 6 && strlength(string(frameTitle)) > 0
    title(frameTitle)
end

drawnow

if nargin >= 7 && pauseDuration > 0
    pause(pauseDuration)
end

end