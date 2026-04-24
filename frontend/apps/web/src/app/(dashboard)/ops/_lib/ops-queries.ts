import type { QueueRow } from "@/types/ops";

const QUEUE_DEPTH_WARN_THRESHOLD = 2000;

export { QUEUE_DEPTH_WARN_THRESHOLD };

export function getQueueSnapshot(): QueueRow[] {
  return [
    {
      domainId: "dom-001",
      domainName: "m47.dispatch.internal",
      queueName: "send.m47.dispatch.internal",
      workerCount: 2,
      queueDepth: 0,
      oldestQueuedAgeSeconds: null,
      denialsPerMinute: 0,
      updatedAt: "2026-04-24T09:58:00Z",
    },
    {
      domainId: "dom-002",
      domainName: "m48.dispatch.internal",
      queueName: "send.m48.dispatch.internal",
      workerCount: 4,
      queueDepth: 1240,
      oldestQueuedAgeSeconds: 847,
      denialsPerMinute: 3.2,
      updatedAt: "2026-04-24T09:58:00Z",
    },
    {
      domainId: "dom-003",
      domainName: "m49.dispatch.internal",
      queueName: "send.m49.dispatch.internal",
      workerCount: 1,
      queueDepth: 5820,
      oldestQueuedAgeSeconds: 3601,
      denialsPerMinute: 14.7,
      updatedAt: "2026-04-24T09:58:00Z",
    },
  ];
}
