export type QueueRow = {
  domainId: string;
  domainName: string;
  queueName: string;
  workerCount: number;
  queueDepth: number;
  oldestQueuedAgeSeconds: number | null;
  denialsPerMinute: number;
  updatedAt: string;
};
