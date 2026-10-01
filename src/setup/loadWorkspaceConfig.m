% Function for loading a workspace YAML config file into a workspace object
function workspace = loadWorkspaceConfig(configFile)

if nargin < 1
    error("A workspace config file path is required.")
end

configFile = string(configFile);

if ~isfile(configFile)
    error("Workspace config file not found: " + configFile)
end

workspace = readSimpleYaml(configFile);

% make sure the config defines every workspace field
requiredFields = ["size", "sourceregion", "movedregion", "movedSpacing", ...
    "material", "surfaceHeight", "coeffFriction", "youngsModulus", ...
    "poissonRatio", "density", "surfaceEnergy"];

missingFields = requiredFields(~isfield(workspace, requiredFields));
if ~isempty(missingFields)
    error("Workspace config is missing fields: " + strjoin(missingFields, ", "))
end

if numel(workspace.size) ~= 3 || ...
        numel(workspace.sourceregion) ~= 4 || ...
        numel(workspace.movedregion) ~= 4
    error("size, sourceregion, and movedregion must contain 3, 4, and 4 values.")
end

end


% Minimal YAML reader for flat workspace configs:
%   key: value               (number, bare or quoted string)
%   key: [v1, v2, v3]        (inline list of numbers)
function cfg = readSimpleYaml(configFile)

lines = readlines(configFile);
cfg = struct();

for i = 1:numel(lines)

    line = strtrim(lines(i));

    % skip blank lines, comments, and document separators
    if line == "" || line == "---" || startsWith(line, "#")
        continue
    end

    if startsWith(line, "-")
        error("YAML lists are not supported in workspace configs (line: " + line + ")")
    end

    colonIndex = strfind(line, ":");
    if isempty(colonIndex)
        error("Unsupported YAML line: " + line)
    end

    key = strtrim(extractBefore(line, colonIndex(1)));
    value = strtrim(extractAfter(line, colonIndex(1)));

    % strip inline comments
    commentIndex = strfind(value, "#");
    if ~isempty(commentIndex)
        value = strtrim(extractBefore(value, commentIndex(1)));
    end

    cfg.(key) = parseSimpleYamlValue(value, line);

end

end


% Convert one YAML value (number, string, or inline numeric list)
function value = parseSimpleYamlValue(text, line)

if startsWith(text, "[") && endsWith(text, "]")

    % inline list of numbers
    inner = strtrim(extractBetween(text, 2, strlength(text) - 1));

    if inner == ""
        value = [];
        return
    end

    parts = strtrim(split(inner, ","));

    value = zeros(1, numel(parts));
    for k = 1:numel(parts)
        value(k) = str2double(parts(k));
    end

    if any(isnan(value))
        error("Unsupported YAML list value in line: " + line)
    end

elseif startsWith(text, """") || startsWith(text, "'")

    % quoted string
    value = string(extractBetween(text, 2, strlength(text) - 1));

else

    number = str2double(text);
    if isnan(number)
        value = string(text);   % bare string
    else
        value = number;
    end

end

end
