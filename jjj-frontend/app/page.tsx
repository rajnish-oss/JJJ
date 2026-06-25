"use client";
import Radar from "./components/radar";
import InfoCard from "./components/infoCard";
import { useEffect, useState, useRef } from "react";

export default function Home() {
  const [messages, setMessages] = useState<any>(null);
  const [location, setLocation] = useState<any>(null);
  
  // Use a ref for the WebSocket to persist it across renders without triggering effects
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 1. Initialize standard Native WebSocket (Matches FastAPI)
    ws.current = new WebSocket("ws://localhost:8000/ws");

    ws.current.onopen = () => {
      console.log("Connected to backend WebSocket cleanly.");
    };

    ws.current.onmessage = (event) => {
      // Native WebSockets receive strings, must parse to JSON
      const data = JSON.parse(event.data);
      console.log("Received from server:", data);
      
      // Append new messages to the existing array safely
      setMessages(data);
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  console.log(messages && messages.report)

  useEffect(() => {
    if (!navigator.geolocation) return;

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        // 2. Map strictly to what the backend expects ("lat" and "lon")
        const currentPosition = {
          lat: position.coords.latitude,
          lon: position.coords.longitude, 
        };

        console.log("Current Position:", currentPosition);

        // Update UI state for visual purposes
        setLocation({
            ...currentPosition,
            accuracy: position.coords.accuracy,
            timestamp: new Date(position.timestamp).toLocaleTimeString(),
        });

        // 3. Send data directly to bypass React's async state delay
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify(currentPosition));
        }
      },
      (error) => {
        console.error("Geolocation Error:", error);
        if (error.code === 1) {
          alert("To use this feature, please enable location services.");
        }
      },
      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 5000,
      }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  return (
    <main className="flex bg-black h-full flex-1 items-center justify-center p-8">
      
      <div>
      {messages === null ? (
        <Radar />
      ) : (
        <>
          {messages.error && (
              <div className="bg-red-900 text-white p-4 rounded">
                Server Message: {messages.error}
              </div>
          )}
          {messages.report && (
              <InfoCard Data={messages.report} />
          )}
        </>
      )}
    </div>

    </main>
  );
}