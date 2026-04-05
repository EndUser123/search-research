
export enum DownloadStatus {
  DOWNLOADING = 'Downloading',
  QUEUED = 'Queued',
  COMPLETED = 'Completed',
  ERROR = 'Error'
}

export interface DownloadItem {
  id: string;
  channel: string;
  status: DownloadStatus;
  progress: number;
  eta: string;
}

export enum LogLevel {
  INFO = 'INFO',
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR',
  WARN = 'WARN'
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
}
