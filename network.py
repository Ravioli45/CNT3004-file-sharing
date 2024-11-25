# Not complete still working on it, but adding it just becasue

import pandas as pd
import time 
import threading

class Analyze:
    def __init__(self):
        self.stats = {'FileName' : [], 'DownloadTime' : [], 'DownloadRate' : [], 'UploadTime': [], 'UploadSpeed': []}
        self.df = pd.DataFrame(self.stats)
        self.lock = threading.Lock()

    def analyze_stats(self, FileName, DownloadSize, UploadSize):
        t = threading.Thread(target=self.analyze, args= (FileName, UploadSize, DownloadSize))
        t.start()

    def analyze(self, FileName, DownloadSize, UploadSize):
        try: 
            StartUpload = time.time()
            time.sleep(UploadSize/1000)
            UploadEnding = time.time()

            StartDownload = time.time()
            time.sleep(DownloadSize/1000)
            DownloadEnd = time.time()

            UploadTime = UploadEnding - StartUpload
            DownloadTime = DownloadEnd - StartDownload
            UploadSpeed = DownloadSize / DownloadTime

            with self.lock:
                self.df = self.df.append({ 'FileName': FileName, 'UploadTime': UploadTime, 'DownloadTime': DownloadTime, 'UploadSpeed': UploadSpeed, 'DownloadRate': DownloadRate}, ignore_index = True)

        except Exception as ex:
            print(f"ERROR: Analyzing File {FileName}: {ex}")
    
    def Print(self):
        with self.lock:
            print(self.df)

    def Save(self, FilePath = "NetworkAnalysis.csv"):
        with self.lock:
            self.df.to_csv(FilePath, index = False)
            print(f"Report was saved to {FilePath}")

Analyzer = Analyze()
Analyzer.start_analysis("File1.txt", 1000, 500)
Analyzer.start_analysis("File2.mp4", 50000, 20000)

time.sleep(10)
Analyzer.Print()
Analyzer.Save()
