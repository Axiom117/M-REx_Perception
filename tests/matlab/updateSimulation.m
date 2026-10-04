function updateSimulation(varargin)
% Headless shadow of src/visualization/updateSimulation.m for parity dumps.
%
% tests/matlab is added to the path after src/** by dumpFixture.m, so this
% no-op version wins over the renderer (clf/drawnow/pause) when the dump runs.
% It keeps the trace purely numeric and figure-free; no src file is touched.
%
% While MREX_TRACE_REC.active is true it records the per-step tool pose and
% the attached embryo's pose that moveTool.m would have rendered.

global MREX_TRACE_REC

if isempty(MREX_TRACE_REC) || ~MREX_TRACE_REC.active
    return
end

if numel(varargin) < 3
    return
end

embryos = varargin{2};
tool = varargin{3};

MREX_TRACE_REC.toolPositions(end + 1, :) = tool.position';
MREX_TRACE_REC.toolOrientations(end + 1, :) = reshape(tool.orientation, 1, 9);

if isfield(tool, "hasEmbryo") && isfield(tool, "attachedEmbryoID") ...
        && tool.hasEmbryo && tool.attachedEmbryoID > 0
    id = tool.attachedEmbryoID;
    MREX_TRACE_REC.attachedPositions(end + 1, :) = embryos(id).position';
    MREX_TRACE_REC.attachedOrientations(end + 1, :) = ...
        reshape(embryos(id).orientation, 1, 9);
end

end
