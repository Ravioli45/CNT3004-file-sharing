import pandas as pd
import time
import threading

class Analyze:
    def __init__(self):
        self.stats = {
            'FileName': [],
            'DownloadTime': [],
            'DownloadRate': [],
            'UploadTime': [],
            'UploadSpeed': [],
            'ResponseTime': []
        }
# Create DataFrame to hold the stats
        self.df = pd.DataFrame(self.stats)
        self.lock = threading.Lock()


# Collecting statistics
    def analyze_stats(self, FileName, DownloadSize, UploadSize, ResponseTime, UploadTime=None, DownloadTime=None):
       
        upload_speed = UploadSize / UploadTime if UploadTime else None
        download_rate = DownloadSize / DownloadTime if DownloadTime else None

        new_row = pd.DataFrame([{
            'FileName': FileName,
            'UploadTime': UploadTime,
            'DownloadTime': DownloadTime,
            'UploadSpeed': upload_speed,
            'DownloadRate': download_rate,
            'ResponseTime': ResponseTime
        }])

#Using concat instead of append due to warning in SSH browser
        with self.lock:
            self.df = pd.concat([self.df, new_row], ignore_index=True)

    def save(self, FilePath=None):
        if FilePath is None:
            FilePath = f"NetworkAnalysis_{int(time.time())}.csv"  
        with self.lock:
            self.df.to_csv(FilePath, index=False)
            print(f"Report saved to {FilePath}")

    def print_stats(self):
        with self.lock:
            print(self.df)

# Testing
if __name__ == "__main__":
    analyzer = Analyze()

    analyzer.analyze_stats("File1.txt", 1000, 500, 0.05, UploadTime=0.5, DownloadTime=1.2)
    analyzer.analyze_stats("File2.mp4", 50000, 20000, 0.12, UploadTime=2.0, DownloadTime=3.5)

    analyzer.print_stats()

    analyzer.save()
