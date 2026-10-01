% Function for adding the stop button and the close behavior to the
% simulation figure. Safe to call again after every clf.
function addStopControls(fig)

if nargin < 1 || isempty(fig)
    fig = gcf;
end

% closing the figure stops the simulation instead of popping back up
set(fig, "CloseRequestFcn", @(~, ~) closeSimulationFigure(fig));

% create the stop button if it is not present (clf removes it)
if isempty(findobj(fig, "Tag", "StopSimulationButton"))

    uicontrol(fig, ...
        "Style", "pushbutton", ...
        "String", "Stop Simulation", ...
        "Tag", "StopSimulationButton", ...
        "Units", "normalized", ...
        "Position", [0.78, 0.94, 0.21, 0.05], ...
        "FontSize", 9, ...
        "Callback", @(~, ~) requestStop());

end

end


% Close callback: request a stop, then let the window close
function closeSimulationFigure(fig)

requestStop();
delete(fig);

end


% Set the shared stop flag that simulationStopped() reads
function requestStop()

setappdata(0, "TaskFlowStopSimulation", true);

end
