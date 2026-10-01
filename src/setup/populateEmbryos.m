% Function for populating the workspace with randomly arranged embryos
function embryos = populateEmbryos(workspace, numEmbryos, minSpacing)

if nargin < 2 || isempty(numEmbryos)
    numEmbryos = 6;
end

if nargin < 3 || isempty(minSpacing)
    minSpacing = 1.0;
end

% source region of the workspace (same mapping as pixelToWorkspace)
sourceX = workspace.sourceregion(1);
sourceY = workspace.sourceregion(2);
sourceW = workspace.sourceregion(3);
sourceH = workspace.sourceregion(4);

embryos = struct([]);

for i = 1:numEmbryos

    % draw random positions until the candidate is far enough
    % from every embryo that has already been placed
    position = [];
    for attempt = 1:1000

        candidate = [ ...
            sourceX + rand*sourceW; ...
            sourceY + rand*sourceH; ...
            0.1];

        if isempty(embryos) || ...
                all(vecnorm([embryos.position] - candidate, 2, 1) >= minSpacing)

            position = candidate;
            break

        end

    end

    % best effort: accept the last candidate if no spot was free
    if isempty(position)
        position = candidate;
    end

    embryo = struct();

    embryo.state = "free";
    embryo.attempts = 0;
    embryo.pickedSuccessfully = false;

    embryo.shape = 'ellipsoid';
    embryo.width = 0.2;
    embryo.length = 0.5;
    embryo.height = 0.2;

    embryo.confidence = 1.0;

    embryo.position = position;

    % random orientation around the vertical axis
    yaw = 2*pi*rand;

    Rz = [cos(yaw) -sin(yaw) 0; sin(yaw) cos(yaw) 0; 0 0 1];
    embryo.orientation = Rz;
    embryo.pose = [embryo.orientation embryo.position; 0 0 0 1];

    if i == 1
        embryos = embryo;
    else
        embryos(i) = embryo;
    end

end

end
