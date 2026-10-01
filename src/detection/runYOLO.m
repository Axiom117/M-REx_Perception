function runYOLO(imagePath, csvFile)

% Locate project folders relative to this file (src/detection/runYOLO.m)
thisFolder = fileparts(mfilename("fullpath"));
projectFolder = fileparts(fileparts(thisFolder));

pythonScript = fullfile(projectFolder, "python", "extract_obb_data.py");

% Python interpreter from the project virtual environment (with a system fallback)
if ispc
    venvPython = fullfile(projectFolder, "python", ".venv", "Scripts", "python.exe");
    fallbackPython = "python";
else
    venvPython = fullfile(projectFolder, "python", ".venv", "bin", "python3");
    fallbackPython = "python3";
end

if isfile(venvPython)
    pythonExe = venvPython;
else
    pythonExe = fallbackPython;
end

command = sprintf('"%s" "%s" "%s" "%s"', pythonExe, pythonScript, imagePath, csvFile);

status = system(command);

if status ~= 0
    error("Python script failed to run. Check the Python environment in python/.venv.")
end

end