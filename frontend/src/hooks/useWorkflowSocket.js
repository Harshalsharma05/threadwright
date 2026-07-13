import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

export function useWorkflowSocket(workflowRunId) {
    const [nodeStatuses, setNodeStatuses] = useState({});
    const wsRef = useRef(null);

    useEffect(() => {
        if (!workflowRunId) return;

        let isSubscribed = true;

        // 1. Fetch existing state from the database
        const fetchInitialState = async () => {
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/runs/${workflowRunId}`);
                if (isSubscribed && res.data.nodes) {
                    const initialStatuses = {};
                    // Convert { search_news: { status: "done" } } to { search_news: "done" }
                    for (const [nodeId, data] of Object.entries(res.data.nodes)) {
                        initialStatuses[nodeId] = data.status;
                    }
                    // Only update if we haven't already received newer WS events
                    setNodeStatuses((prev) => ({ ...initialStatuses, ...prev }));
                }
            } catch (err) {
                console.error("Failed to fetch initial run state:", err);
            }
        };

        fetchInitialState();

        // 2. Open the WebSocket to listen for live updates
        const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/${workflowRunId}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log(`Connected to Threadwright WS for run: ${workflowRunId}`);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.node_id && data.status) {
                    setNodeStatuses((prev) => ({
                        ...prev,
                        [data.node_id]: data.status,
                    }));
                }
            } catch (err) {
                console.error('Failed to parse WS message:', err);
            }
        };

        return () => {
            isSubscribed = false;
            if (ws.readyState === 1) {
                ws.close();
            }
        };
    }, [workflowRunId]);

    return nodeStatuses;
}