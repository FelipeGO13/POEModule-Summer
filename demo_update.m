%{
%   Created on April 1, 2015
%   Renamed from test_update.m on April 2, 2015
%   Last modified on April 16, 2015 by Yaodong Yu
%
%   @author: Zhen Hong
%
%   This is the update script for Octave plotting program as a part of demonstration of
%       UBC ECE 2014 Capstone Project #94
%
%   TODO: this script should be more dynamic in terms of processing various length of params
%}

function [PARA] = demo_update(fName, newData, whatToPlot)
%{
% This function updates the Octave plot with the new data passed in, and saves it in both temporary datafile (.txt)
%   and the database file (.mat)
%
% param str fName: full name of the .txt data file
% param list newData: set of new sensor data
% param int whatToPlot: an enum indicating which sensor data is passed in for plotting
%
% FIXME: this script needs lots of fixes in dynamically accepting parameter to plot and deciding what to plot
% newData is in the format of :
% PARA1 PARA2 ... PARA8 yyyy mm dd hh minmin ss.ssss
% First 8 params correspond to acceleration X, Y, Z, temperature, humidity, motion, joystick X, Y
% Last 6 params correspond to time parameters (year, month, day, hour, minute, second)
% Any parameter with value >= 9999, or equal 'NaN' are invalid or None data
% e.g. [1, 2, 3, 55, 0, 9999, 4, NaN, 6, 2015, 4, 1, 1, 2, 3.1234]
%
% whatToPlot value are matched as the following:
%   1. Joystick X and Y
%   2. Temperature
%   3. Humidity
%   4. Acceleration X
%   5. Acceleration Y
%   6. Acceleration Z
%   7. Motion
%
% Example Usage:
% ``filename = 'data.txt';``
% ``data_update = [1, 2, 3, 55, 0, 9999, 4, NaN, 6, 2015, 4, 1, 1, 2, 3.1234];``
% ``whatToPlot = 2;``
% ``demo_update(filename, data_update, whatToPlot);``
% or simply:
% ``demo_update('test.txt', [1, 2, 3, 55, 0, 9999, 4, NaN, 6, 2015, 4, 1, 1, 2, 3.1234], 2);``
%}

    % TODO: this matching is very messy, need some clean-up
    switch whatToPlot
        case 1 % Joystick
            toPlot = 7;
        case 2 % Temperature
            toPlot = 4;
        case 3 % Humidity
            toPlot = 5;
        case 4 % Acceleration X
            toPlot = 1;
        case 5 % Acceleration Y
            toPlot = 2;
        case 6 % Acceleration Z
            toPlot = 3;
        case 7 % Motion
            toPlot = 6;
    end

    SECPERSEC  = 1;
    SECPERMIN  = 60*SECPERSEC;
    SECPERHOUR = 60*SECPERMIN;
    SECPERDAY  = 24*SECPERHOUR;
    SECPERMON  = 30*SECPERDAY;
    SECPERYEAR = 12*SECPERMON; %#ok<NASGU>

    time_inst = newData(end-2)*SECPERHOUR + newData(end-1)*SECPERMIN + newData(end);

    % Joystick moving range constants by experiment
    js_Xmin = 260; js_Xmax = 763; %js_xcentre = 516;
    js_Ymin = 253; js_Ymax = 769; %js_ycentre = 510;

    % Invalidate unreasonable numbers (>= 9999 or 'NaN')
    newData(~(newData < 9999)) = NaN;
    
    [~, name, ext] = fileparts(fName);
    fNameToSave = strcat(name, '.mat');
    
    % Check for validity
    if(~strcmp(ext, '.txt'))
        error('Expecting file name with ".txt" extension');
    elseif(~exist(fNameToSave, 'file'))
        error('No corresponding ".mat" file generated yet. Should initialize first.');
    end
    
    data = load(fNameToSave);
    check_empty = fieldnames(data);

    % Call init script if database file is empty
    if(isempty(data.(check_empty{1})))
        save(fName, 'newData', '-ascii');
        demo_init(fName);
    else
        name_para = fieldnames(data);
        PARA = data.(name_para{1});

        numpara = length(PARA);  % number of parameters
        temp_data = newData(1:numpara);
        logical_temp = temp_data < 9999;

        logical data = temp_data(logical_temp);
        logical_PARA = PARA(logical_temp);
        numupdate = sum(logical_temp);
        for i = 1:numupdate
            logical_PARA{i} = [logical_PARA{i}; [logical_data(i), time_inst]];
        end
        
        PARA(logical_temp) = logical_PARA;
        
        switch toPlot
            case 7  % Joystick
                x = PARA{7}(end, 1); y = PARA{8}(end, 1);
                plot(x, y, 'r.', 'markersize', 40); grid;
                xlabel('Position in x'); ylabel('Position in y');
                title('Joystick Position'); set(gca, 'FontSize', 12);
                axis([js_Xmin, js_Xmax, js_Ymin, js_Ymax]);
            otherwise
                if(~isempty(PARA{toPlot}))
                    x = PARA{toPlot}(:, end); y = PARA{toPlot}(:, 1);
                    plot(x, y); grid;
                    xlabel('Time Elapsed (s)'); set(gca,'FontSize',12);
                    if(x(end) > x(1))
                        xlim([x(1), x(end)]);
                    elseif(x(end) < x(1))
                        error('Error in time calculation. (x(end) <= x(1))');
                    end
                end
        end
        
        switch toPlot
            case 1
                title('Acceleration Profile in x'); ylabel('Acceleration in x (ms^{-2})'); 
            case 2
                title('Acceleration Profile in y'); ylabel('Acceleration in y (ms^{-2})');
            case 3 
                title('Acceleration Profile in z'); ylabel('Acceleration in z (ms^{-2})');
            case 4
                title('Temperature Profile'); ylabel('Temperature (Celcius)');
            case 5
                title('Humidity Profile'); ylabel('Relative Humidity (%)');
            case 6
                title('Motion Detection'); ylabel('Motion Detected? (1 for yes, 0 otherwise)');
        end
        
        save(fNameToSave, 'PARA', '-v6');
    end
        
end

