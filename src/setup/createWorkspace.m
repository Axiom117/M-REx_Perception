% Function for creating the workspace for the embryo simulation.
% Workspace properties are loaded from a YAML config file in the
% project's config/workspace folder (selected by name).
function workspace = createWorkspace(configName)

if nargin < 1 || isempty(configName)
    configName = "default";
end

configName = string(configName);
configName = erase(configName, [".yaml", ".yml"]);

% locate project folders relative to this file (src/setup/createWorkspace.m)
thisFolder = fileparts(mfilename("fullpath"));
projectFolder = fileparts(fileparts(thisFolder));

configFolder = fullfile(projectFolder, "config", "workspace");

% use the first matching config file that exists
configFile = "";
for extension = [".yaml", ".yml"]
    candidate = fullfile(configFolder, configName + extension);
    if isfile(candidate)
        configFile = candidate;
        break
    end
end

if configFile == ""
    error("Workspace config not found: " + fullfile(configFolder, configName + ".yaml"))
end

workspace = loadWorkspaceConfig(configFile);

end