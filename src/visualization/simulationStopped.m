% Function checking whether the running simulation was asked to stop
% (set by the stop button or by closing the simulation figure)
function tf = simulationStopped()

tf = isappdata(0, "TaskFlowStopSimulation") && ...
    getappdata(0, "TaskFlowStopSimulation");

end
