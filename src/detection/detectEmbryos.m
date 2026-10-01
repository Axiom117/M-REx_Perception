function embryos = detectEmbryos(imagePath, workspace)

% Prediction CSV written by the Python YOLO script (project root)
thisFolder = fileparts(mfilename("fullpath"));
projectFolder = fileparts(fileparts(thisFolder));
csvFile = fullfile(projectFolder, "obb_predictions_v3.csv");

if isfile(csvFile)
    delete(csvFile);
end

runYOLO(imagePath, csvFile);

if ~isfile(csvFile)
    error("YOLO did not create the expected prediction CSV.")
end

embryos = createEmbryoFromYOLO(csvFile, workspace);

end