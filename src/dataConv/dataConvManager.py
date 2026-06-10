import datetime
import os
import cv2
import time
import cartopy.crs as ccrs
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import nidaqmx
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from nidaqmx.constants import LineGrouping
import matplotlib
from skyfield.api import load
from convClient import Client
from utils import ProcessData
import atexit
matplotlib.use('Qt5Agg')
import sys
import threading
import json
import configparser
import tkinter as tk
from datetime import datetime
from queue import Queue
from live_mapbox_display import start_display, stop_display



import pygame
from pyvidplayer2 import Video


class DataConv:
    def __init__(self):
        
        config=configparser.ConfigParser()
        config.read('DataConv_config.ini')
        
        self.demo_video_PATH=config.get('DATA_CONV_MANAGER', 'demo_video_PATH')
        satellite_view_video_path = self.demo_video_PATH 
        self.is_video_on = False
        self.demo = False
        self.connect_to_api = False
        self.video_thread = threading.Thread(target=self.play_video_fullscreen, args=(satellite_view_video_path,))
        self.firstTimestampReceived = {'received': False}
        self.mapbox_coord_queue = Queue()

        self.com_with_manager_PORT=config.getint('DATA_CONV_MANAGER', 'com_with_manager_PORT')
        
        self.SOLAR_INTENSITY_SCALE0_MIN=config.getfloat('DATA_CONV_MANAGER', 'SOLAR_INTENSITY_SCALE0_MIN')
        self.SOLAR_INTENSITY_SCALE0_MAX=config.getfloat('DATA_CONV_MANAGER', 'SOLAR_INTENSITY_SCALE0_MAX')
        self.SOLAR_INTENSITY_SCALE1_MIN=config.getfloat('DATA_CONV_MANAGER', 'SOLAR_INTENSITY_SCALE1_MIN')
        self.SOLAR_INTENSITY_SCALE1_MAX=config.getfloat('DATA_CONV_MANAGER', 'SOLAR_INTENSITY_SCALE1_MAX')
        
        self.SUN_01=config.get('DATA_CONV_MANAGER', 'SUN_01')
        self.SUN_02=config.get('DATA_CONV_MANAGER', 'SUN_02')
        
        self.HELMHOLTZ_COIL_X=config.get('DATA_CONV_MANAGER', 'HELMHOLTZ_COIL_X')
        self.HELMHOLTZ_COIL_Y=config.get('DATA_CONV_MANAGER', 'HELMHOLTZ_COIL_Y')
        self.HELMHOLTZ_COIL_Z=config.get('DATA_CONV_MANAGER', 'HELMHOLTZ_COIL_Z')
        
        self.RELAY=config.get('DATA_CONV_MANAGER', 'RELAY')
        
        self.is_demo_running=config.getboolean('DATA_CONV_MANAGER', 'is_demo_running')
        self.full_cycleVideo_PATH=config.get('DATA_CONV_MANAGER', 'full_cycleVideo_PATH')

        resistance_r=config.getfloat('DATA_CONV_MANAGER', 'resistance_r')
        resistance_l=config.getfloat('DATA_CONV_MANAGER', 'resistance_l')
        rmm_x=config.getfloat('DATA_CONV_MANAGER', 'rmm_x')
        rmm_y=config.getfloat('DATA_CONV_MANAGER', 'rmm_y')
        rmm_z=config.getfloat('DATA_CONV_MANAGER', 'rmm_z')
        n_x=config.getfloat('DATA_CONV_MANAGER', 'n_x')
        n_y=config.getfloat('DATA_CONV_MANAGER', 'n_y')
        n_z=config.getfloat('DATA_CONV_MANAGER', 'n_z')
        reset_x=config.getfloat('DATA_CONV_MANAGER', 'reset_x')
        reset_y=config.getfloat('DATA_CONV_MANAGER', 'reset_y')
        reset_z=config.getfloat('DATA_CONV_MANAGER', 'reset_z')
        # Consts
        self.SOLAR_INTENSITY_RANGE = None
        
        # Solar intensity Configuration
        self.SOLAR_INTENSITY_SCALE0 = (self.SOLAR_INTENSITY_SCALE0_MIN, self.SOLAR_INTENSITY_SCALE0_MAX)
        self.SOLAR_INTENSITY_SCALE1 = (self.SOLAR_INTENSITY_SCALE1_MIN, self.SOLAR_INTENSITY_SCALE1_MAX)  
        
        # Magnetic Field Configuration
        self.RESISTANCE = resistance_r + resistance_l
        self.MAGNETIC_FIELD_CONVERSION = [rmm_x / (n_x * 0.8992 * 1000000), rmm_y / (n_y * 0.8992 * 1000000), rmm_z / (n_z * 0.8992 * 1000000)] # R [mm] / (N * ((4/5)^1.5) * mu_0) 
        self.RESET_MAGNETIC_FIELD = [reset_x, reset_y, reset_z] ####################################################################################
        atexit.register(self.cleanup)

        # DAQ Configuration
        self.analog_output_channels=[self.SUN_01, 
                                       self.SUN_02, 
                                       self.HELMHOLTZ_COIL_X, 
                                       self.HELMHOLTZ_COIL_Y,
                                       self.HELMHOLTZ_COIL_Z]
        
        self.digital_output_channel=self.RELAY

        self.ts = load.timescale()
        self.digital_state = None
        
       
 

        with open('DataConv_config.ini', 'w') as configfile:
            config.write(configfile)

        
        
    def cleanup(self):
        self.output_to_daq([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], True) # The relay start working and the lamps turn off 

    @staticmethod
    def get_satellite(self):
        found_satellites = load.tle_file(self.station_url)
        by_name = [sat for sat in found_satellites if sat.name == self.satellite_name]
        loaded_satellite = by_name[0]
        print(f"Loaded {loaded_satellite}")

        return loaded_satellite
    
    def process_solar_intensity(self, solar_intensity, scale):
        # print(solar_intensity)
        from_min, from_max = self.SOLAR_INTENSITY_RANGE
        to_min, to_max = scale
        
        if solar_intensity != 0:
                # Clamp the value to the original range
            solar_intensity = np.clip(solar_intensity, from_min, from_max)
            
            # Map the value from the original range to the new range
            scaled_value = (solar_intensity - from_min) / (from_max - from_min)
            solar_in = to_min + (scaled_value * (to_max - to_min))
        else:
            solar_in = np.array(0.0)
            
        return solar_in


    def convert_magnetic_field(self, magnetic_field):
        # Convert magnetic field data to current in mA
        return (((magnetic_field * self.MAGNETIC_FIELD_CONVERSION)*(self.RESISTANCE))+self.RESET_MAGNETIC_FIELD) # V = B * const * (R + jwL) , ### (w = 10k) , (I = B * const) ###

    def output_to_daq(self, analog_data, digital_data):
        with nidaqmx.Task() as task_ao:
            
            task_ao.ao_channels.add_ao_voltage_chan(self.analog_output_channels[0])  # LED NUMBER 2
            task_ao.ao_channels.add_ao_voltage_chan(self.analog_output_channels[1])  # LED NUMBER 1
            task_ao.ao_channels.add_ao_voltage_chan(self.analog_output_channels[2])  # MAGNETIC FIELD AXIS X
            task_ao.ao_channels.add_ao_voltage_chan(self.analog_output_channels[3])  # MAGNETIC FIELD AXIS Y
            task_ao.ao_channels.add_ao_voltage_chan(self.analog_output_channels[4])  # MAGNETIC FIELD AXIS Z
            task_ao.write([analog_data[0], analog_data[1], analog_data[2], analog_data[3], analog_data[4]], auto_start=True)  # Writing the data

        # Digital output
        with nidaqmx.Task() as task_do: 
            task_do.do_channels.add_do_chan(self.digital_output_channel, line_grouping=LineGrouping.CHAN_PER_LINE)
            task_do.write(digital_data, auto_start=True)

    def process_magnetic_fields(self, row_data):
        magnetic_field = np.array([
            row_data['Magnetic Field X'],
            row_data['Magnetic Field Y'],
            row_data['Magnetic Field Z']
        ])
        magnetic_field_volt = self.convert_magnetic_field(magnetic_field)
        return magnetic_field_volt

    def deserialize_time(self, time_tuple):
        return self.ts.utc(*time_tuple)

    def start(self):
        
        
        # Initialize the digital state to False, indicating that the relay is not active
        self.digital_state = False 

        # Set parameters for the connection with the manager computer
        manager_IP = sys.argv[1]
        if sys.argv[2]=="True":
            self.connect_to_api =True 
        client = Client(manager_IP, self.com_with_manager_PORT, "orbital")
        
        # Connect to the manager computer
        client.run()
        
        # Retrieve necessary data from the manager computer
        # This includes TLE data (for satellite orbital information), timestamp data, and a new solar intensity rang
        data = client.prep()
        tle_data, time_data, new_range,demo = data
        self.SOLAR_INTENSITY_RANGE = (new_range[0], new_range[1])
        process_data = ProcessData(tle_data, self.ts)
        self.demo=demo
        if self.demo:
            # Open the view-on-earth video on Full Screen
            self.is_video_on = True
            self.video_thread.start()
            self.SIM_INIT_TIME = time_data
            self.SOLAR_INTENSITY_SCALE0_MIN = 0.5
            self.SOLAR_INTENSITY_SCALE0_MAX = 0.7
            self.SOLAR_INTENSITY_SCALE1_MIN = 0.5
            self.SOLAR_INTENSITY_SCALE1_MAX = 0.7
            self.SOLAR_INTENSITY_SCALE0 = (self.SOLAR_INTENSITY_SCALE0_MIN, self.SOLAR_INTENSITY_SCALE0_MAX)
            self.SOLAR_INTENSITY_SCALE1 = (self.SOLAR_INTENSITY_SCALE1_MIN, self.SOLAR_INTENSITY_SCALE1_MAX)
        
        
        if not self.demo and self.connect_to_api:
            start_display(self.mapbox_coord_queue)

        

        while True:
            try:
                # send message(empty) to and receive data from the manager computer
                data_from_manager = client.execute()
                
                deserialized_time = self.deserialize_time(data_from_manager["data"]["time"])
                
                
                if self.firstTimestampReceived['received'] is False:
                    self.firstTimestampReceived['received'] = True
                    self.firstTimestampReceived['time'] = data_from_manager["data"]["time"]
                    
                
                # Use the deserialized timestamp to retrieve the corresponding row of data
                # which contains data such as latitude, lontitude, solar intensity and the
                row_data = process_data.get_row(deserialized_time)
                
                # Send coordinates to display module
                if not self.demo and self.connect_to_api:
                    lat = row_data.get('Latitude')
                    lon = row_data.get('Longitude')
                    if lat is not None and lon is not None:
                        self.mapbox_coord_queue.put((lat, lon))
                # Process the solar intensity data using two different scaling factors.
                solar_intensity0 = self.process_solar_intensity(row_data['Solar Intensity'], self.SOLAR_INTENSITY_SCALE0)
                solar_intensity1 = self.process_solar_intensity(row_data['Solar Intensity'], self.SOLAR_INTENSITY_SCALE1)
                
                # Process the magnetic field data and convert it into voltage values.
                magnetic_field_volt = self.process_magnetic_fields(row_data)

                # Combine the processed solar intensity and magnetic field data into a single list for output.
                analog_data = [solar_intensity0.tolist(), solar_intensity1.tolist()] + magnetic_field_volt.tolist()
                
                # Send the processed analog data and the current digital state to the DAQ system for output.
                self.output_to_daq(analog_data, self.digital_state)
                                
                # Check if the message includes a "stop" command. If so, exit the program.
                if "stop" in data_from_manager['data']:
                    #self.cleanup()
                    sys.exit()
                    
            except KeyError as e:
                print("An Error Occured...")
                print(e)
                continue
            
    
            
   

    def play_video_fullscreen(self, video_path):
        # Initialize Pygame
        pygame.init()

        # Load the video
        vid = Video(video_path)
        while True:
            if hasattr(self, 'firstTimestampReceived') and 'time' in self.firstTimestampReceived:
                break
        
        timeDiffrence = self.calculateTimeDiffrence()
        # print(f"Time difference: {timeDiffrence} seconds")
        
        startFromThisSecond = 6
        
        if timeDiffrence > 250 :
            startFromThisSecond += 12
        
        vid.seek(startFromThisSecond)

        # Get screen resolution
        info = pygame.display.Info()
        screen_width, screen_height = info.current_w, info.current_h

        # Create fullscreen window
        win = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption(vid.name)
        
        pygame.mouse.set_visible(False)
        

        # Main loop to play video
        while vid.active and self.is_video_on:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    vid.stop()
                elif event.type == pygame.KEYDOWN:
                    if pygame.key.name(event.key) == "escape":
                        vid.stop()

            # Get the next frame surface
            if vid._update():
                frame = vid.frame_surf
                if frame:
                    # Scale the frame to fullscreen
                    scaled_frame = pygame.transform.scale(frame, (screen_width, screen_height))
                    win.blit(scaled_frame, (0, 0))
                    pygame.display.update()

            pygame.time.wait(16)  # ~60 fps

        vid.close()
        pygame.quit()
    
    def calculateTimeDiffrence(self,):
        timestamp1 = self.SIM_INIT_TIME
        timestamp2 = self.firstTimestampReceived['time']
        
        dt1 = datetime(*timestamp1[:5], second=int(timestamp1[5]), microsecond=int((timestamp1[5] % 1) * 1_000_000))
        dt2 = datetime(*timestamp2[:5], second=int(timestamp2[5]), microsecond=int((timestamp2[5] % 1) * 1_000_000))
        
        time_diff = (dt2 - dt1).total_seconds()
        
        return time_diff

if __name__ == "__main__":
    try:   
        # Initialize and start the satellite environment, including lamps, the electric field and the satellite-view-video
        data_conv = DataConv()
        data_conv.start()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if not data_conv.demo and data_conv.connect_to_api:
            stop_display()

        if data_conv.demo:
            data_conv.is_video_on = False
            data_conv.video_thread.join()

        
    

