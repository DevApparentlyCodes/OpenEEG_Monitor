import sys
import serial
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from dataclasses import dataclass
from typing import Tuple
from scipy.signal import butter, filtfilt, iirnotch


@dataclass
class EEGConfig:
    port : str = "COM3"
    baud_rate : int = 115200
    sampling_rate : int = 250
    
    buffer_size : int = 1000
    
    window_title : str = "EEG Real Time Monitor"
    window_size : Tuple[int, int] = (1000,500)
    update_interval : int = 50
    
    lowpass_cutoff_frequency : float = 50.0
    notch_frequency : float = 50.0
    filter_order : int = 4
    Q_fac : int = 30




class EEGMonitor:
    def __init__(self, config : EEGConfig = None):
        self.config = config if config else EEGConfig()
        
        self.data_buffer = np.zeros(self.config.buffer_size)
        
        self.serial = serial.Serial(self.config.port, self.config.baud_rate)
        
        
        
        self.b_low, self.a_low = self.create_lowpass_filter()
        self.b_notch, self.a_notch = self.create_iirnotch_filter()
        
        
        self.setup_gui()
        self.setup_timer()
        

    def create_lowpass_filter(self):
        nyq_freq = 0.5 * self.config.sampling_rate
        normal_cutoff = self.config.lowpass_cutoff_frequency / nyq_freq # normalizing everything relative to Nyquist scale of 0 to 1
        return butter(self.config.filter_order, normal_cutoff, btype = "low")
    
    def create_iirnotch_filter(self):
        nyq_freq = 0.5 * self.config.sampling_rate
        normalized_freq = self.config.notch_frequency/nyq_freq
        return iirnotch(normalized_freq, self.config.Q_fac)
    
    
    def apply_filters(self, data):
        data = filtfilt(self.b_notch, self.a_notch, data)
        return filtfilt(self.b_low, self.a_low, data)
    
    def setup_gui(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(title = self.config.window_title)
        self.win.resize(*self.config.window_size)
        
        
        # TIME DOMAIN PLOT
        self.time_plt = self.win.addPlot(title = "Raw EEG Signal")
        self.time_curve = self.time_plt.plot(pen = "y")
        self.time_plt.setLabel('left', 'Amplitude', 'uV')
        self.time_plt.setLabel("bottom", "Time", "s")
        
        
        #FREQUENCY DOMAIN PLOT
        self.win.nextRow()
        self.freqfft_plot = self.win.addPlot(title = "FFT of the Raw EEG Signal")
        self.fft_curve = self.freqfft_plot.plot(pen = "c", fillLevel = 0, fillBrush = (0, 100, 255, 50))
        self.freqfft_plot.setLabel("left", "Amplitude", "uV")
        self.freqfft_plot.setLabel("bottom", "Frequency", "Hz")
        self.freqfft_plot.setXRange(0,60)
    
    
    def setup_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.config.update_interval)

      
    def update(self):
        while self.serial.in_waiting >=2:
            try:
                raw_bytes = self.serial.read(2)
                new_Value = int.from_bytes(raw_bytes, byteorder='little')
                self.data_buffer = np.roll(self.data_buffer, -1)
                self.data_buffer[-1] = new_Value
            except ValueError:
                print(f"Read invalid data : {new_Value}")
            except serial.SerialException as e:
                print(f"Serial Port Exception : {e}")
                self.serial.close()
                return
            except Exception as e:
                print(f"Unexpected error : {e}")
        
        filtered_signal = self.apply_filters(self.data_buffer)
        
        
        #FFT Calculation Part
        
        N = len(filtered_signal)
        hamming_window = np.hamming(N) # smoothens the function down
        fft_signal = np.abs(np.fft.rfft(filtered_signal * hamming_window))
        freq = np.fft.rfftfreq(N, d = 1/self.config.sampling_rate)
        
        
        self.fft_curve.setData(freq[1:], fft_signal[1:])


    def run(self):
        self.win.show()
        sys.exit(self.application.exec_())


if __name__ == "__main__":
    electrode1_monitor = EEGMonitor()
    electrode1_monitor.run()