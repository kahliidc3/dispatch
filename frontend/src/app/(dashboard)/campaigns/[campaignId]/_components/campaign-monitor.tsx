"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import { CampaignHeader } from "./campaign-header";
import { CampaignMetrics } from "./campaign-metrics";
import { MessagesTable } from "./messages-table";
import { MessageDrawer } from "./message-drawer";
import { clientJson } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import {
  getMockCampaignDetail,
  getMockMessagesPage,
  getMockMessageDetail,
} from "@/app/(dashboard)/campaigns/_lib/campaigns-queries";
import type {
  CampaignDetail,
  CampaignMessage,
  CampaignMessageDetail,
  CampaignStatus,
  MessagesPage,
} from "@/types/campaign";
import type { BreakerEntryState } from "@/types/ops";

const POLL_INTERVAL_MS = 15_000;

type CampaignMonitorProps = {
  initialDetail: CampaignDetail;
  initialPage: MessagesPage;
  domainBreakerState?: BreakerEntryState;
  domainId?: string;
};

export function CampaignMonitor({
  initialDetail,
  initialPage,
  domainBreakerState = "closed",
  domainId,
}: CampaignMonitorProps) {
  const [detail, setDetail] = useState<CampaignDetail>(initialDetail);
  const [messages, setMessages] = useState<CampaignMessage[]>(
    initialPage.messages,
  );
  const [nextCursor, setNextCursor] = useState<string | null>(
    initialPage.nextCursor,
  );
  const [statusFilter, setStatusFilter] = useState("");
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isRequeuing, setIsRequeuing] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [messageDetail, setMessageDetail] =
    useState<CampaignMessageDetail | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isHiddenRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const pollDetail = useCallback(() => {
    if (isHiddenRef.current) return;
    // In production this would be a real API call.
    // Here we re-derive from mock data so the detail stays fresh.
    const fresh = getMockCampaignDetail(initialDetail.id);
    setDetail(fresh);
  }, [initialDetail.id]);

  const startPolling = useCallback(() => {
    stopPolling();
    pollTimerRef.current = setInterval(pollDetail, POLL_INTERVAL_MS);
  }, [pollDetail, stopPolling]);

  useEffect(() => {
    if (detail.status === "running") {
      startPolling();
    } else {
      stopPolling();
    }

    return stopPolling;
  }, [detail.status, startPolling, stopPolling]);

  useEffect(() => {
    function handleVisibilityChange() {
      isHiddenRef.current = document.visibilityState === "hidden";
    }
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, []);

  function handleStatusChange(newStatus: CampaignStatus) {
    setDetail((prev) => ({ ...prev, status: newStatus }));
  }

  function handleStatusFilterChange(value: string) {
    setStatusFilter(value);
    const page = getMockMessagesPage(
      detail.id,
      null,
      value || null,
    );
    setMessages(page.messages);
    setNextCursor(page.nextCursor);
  }

  function handleLoadMore() {
    if (!nextCursor || isLoadingMore) return;
    setIsLoadingMore(true);
    try {
      const page = getMockMessagesPage(
        detail.id,
        nextCursor,
        statusFilter || null,
      );
      setMessages((prev) => [...prev, ...page.messages]);
      setNextCursor(page.nextCursor);
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function handleBulkRequeue(ids: string[]) {
    if (isRequeuing) return;
    setIsRequeuing(true);
    try {
      await clientJson(apiEndpoints.campaigns.bulkRequeue(detail.id), {
        method: "POST",
        body: { messageIds: ids },
      });
      toast.success(`${ids.length} message${ids.length === 1 ? "" : "s"} re-queued.`);
      // Optimistically mark as queued
      setMessages((prev) =>
        prev.map((m) =>
          ids.includes(m.id) ? { ...m, status: "queued" as const } : m,
        ),
      );
    } catch {
      toast.error("Re-queue failed. Please retry.");
    } finally {
      setIsRequeuing(false);
    }
  }

  function handleSelectMessage(id: string) {
    setSelectedMessageId(id);
    const found = getMockMessageDetail(detail.id, id);
    setMessageDetail(found);
    setDrawerOpen(true);
  }

  function handleCloseDrawer() {
    setDrawerOpen(false);
    setSelectedMessageId(null);
  }

  return (
    <div className="grid gap-6">
      <CampaignHeader
        detail={detail}
        onStatusChange={handleStatusChange}
        domainBreakerState={domainBreakerState}
        domainId={domainId}
      />
      <CampaignMetrics kpis={detail.kpis} velocityPoints={detail.velocityPoints} />
      <MessagesTable
        messages={messages}
        nextCursor={nextCursor}
        statusFilter={statusFilter}
        onStatusFilterChange={handleStatusFilterChange}
        onLoadMore={handleLoadMore}
        isLoadingMore={isLoadingMore}
        selectedMessageId={selectedMessageId}
        onSelectMessage={handleSelectMessage}
        onBulkRequeue={handleBulkRequeue}
        isRequeuing={isRequeuing}
      />
      <MessageDrawer
        detail={messageDetail}
        open={drawerOpen}
        onClose={handleCloseDrawer}
      />
    </div>
  );
}
