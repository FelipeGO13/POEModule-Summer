%{
%   Created on April 1, 2015
%   Renamed from test_init.m on April 2, 2015
%   Last modified on April 16, 2015 by Yaodong Yu
%
%   @author: Zhen Hong
%
%   This is initialization script for Octave plotting program as a part of demonstration of
%       UBC ECE 2014 Capstone Project #94
%
%   TODO: this script should be more dynamic in terms of processing various length of params
%}

function [PARA] = demo_init(fName)
%{
% This function initializes the plotting program by parsing all existing data entries in .txt data file to
%   .mat Matlab file that serves as a database
%
% param str fName: full name of the .txt data file
%
% Example usage:
% ``filename = 'data.txt';``
% ``demo_init(filename);``
% or simply:
% ``demo_init('test.txt');``
%}

    % Time conversion constants
    n_time_para = 6;
    SECPERSEC  = 1;
    SECPERMIN  = 60*SECPERSEC;
    SECPERHOUR = 60*SECPERMIN;
    SECPERDAY  = 24*SECPERHOUR;
    SECPERMON  = 30*SECPERDAY;
    SECPERYEAR = 12*SECPERMON; %#ok<NASGU>

    [~, name, ext] = fileparts(fName);
    fNameToSave = strcat(name, '.mat');
    if(~strcmp(ext, '.txt'))
        disp('Database file should instead have extension ".txt",');
        disp('looking for corresponding".txt"...');
        fName = strcat(name, '.txt');
    end

    if (~exist(fName, 'file'))
        disp('File does not exist, a new one will be created.');
        temp = [];
        save(fName, 'temp', '-ascii');
    end

    try
        data = load(fName);
    catch
        data = [];
        disp("Unable to load file:"); disp(lasterr);
    end

    if (~isempty(data))
        numrow = size(data, 1);  %#ok<NASGU>     % time instances
        numpara = size(data, 2) - n_time_para;     % parameters

        % Parse each time instance in data file and store in cell format
        PARA = cell(numpara, 1);
        for i = 1:numpara
            TEMP = data(:, i);
            T_TEMP = data(:, end-2)*SECPERHOUR + data(:, end-1)*SECPERMIN + data(:, end);
            LOGIC_TEMP = TEMP < 9999;
            PARA{i} = [TEMP(LOGIC_TEMP), T_TEMP(LOGIC_TEMP)];
        end
    else    % Empty data file (.txt)
        if (~exist(fNameToSave,'file'))
            disp('An empty ".mat" file is also created.');
        end
        disp('Database is empty, please update new data.');
        PARA = [];
    end

    save(fNameToSave, 'PARA', '-v6');

end

