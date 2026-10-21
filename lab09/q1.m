%% Question 1 — Network Throughput and Data Transfer Time
clear; clc; close all;

% Task 1: given values
fileSize_MB  = 24;      % MB (1 MB = 1e6 bytes)
linkCapacity = 20;      % Mbps
usableFactor = 0.75;

% Task 2: effective data rate
effRate_Mbps = linkCapacity * usableFactor;

% Task 3: file size in bits and transfer time
fileSize_bits  = fileSize_MB * 1e6 * 8;
transferTime_s = fileSize_bits / (effRate_Mbps * 1e6);

% Task 6: display
fprintf('File size           : %g MB = %g bits\n', fileSize_MB, fileSize_bits);
fprintf('Effective data rate : %.2f Mbps\n', effRate_Mbps);
fprintf('Transfer time       : %.2f s\n\n', transferTime_s);

% Task 4: repeat for several usable factors
factors  = [0.50 0.60 0.75 0.90 1.00];
effRates = linkCapacity .* factors;
times    = fileSize_bits ./ (effRates * 1e6);

T = table(factors', effRates', times', 'VariableNames', ...
    {'UsableFactor', 'EffectiveRate_Mbps', 'TransferTime_s'});
disp(T);
writetable(T, 'Q01_results.csv');

% Task 5: plot
figure;
plot(factors, times, '-o', 'LineWidth', 1.5, 'MarkerFaceColor', 'b');
grid on;
title('Transfer Time vs Usable Capacity Factor (24 MB, 20 Mbps link)');
xlabel('Usable capacity factor');
ylabel('Transfer time (s)');