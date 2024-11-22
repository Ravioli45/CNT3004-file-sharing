import pandas as pd
import time 
import threading

class Analyze;
    def __init__(self):
        self.stats = {'FileName' : [], 'DownloadTime' : [], 'DownloadRate' : [], 'UploadTime': [], 'UploadSpeed': []} #store network stats
        self.df = pd.DataFrame(self.stats)
        self.lock = threading.Lock() 

    def analyze_stats(self, FileName, DownloadSize, UploadSize):
        t = threading.Thread(target=self.analyze)
        
