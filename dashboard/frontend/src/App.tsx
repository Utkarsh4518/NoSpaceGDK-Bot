import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { User, LogEntry } from "./types";

import Landing from "./pages/Landing";
import GuildSelect from "./pages/GuildSelect";
import DashboardLayout from "./pages/DashboardLayout";
import Overview from "./pages/Overview";
import Settings from "./pages/Settings";
import Music from "./pages/Music";
import Moderation from "./pages/Moderation";
import Tickets from "./pages/Tickets";
import Welcome from "./pages/Welcome";
import AIConfigPage from "./pages/AIConfig";
import Logs from "./pages/Logs";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Configure Axios defaults to support secure credentials cookies
  axios.defaults.withCredentials = true;

  useEffect(() => {
    // 1. Fetch Session User Profile
    axios
      .get("/api/auth/me")
      .then((res) => {
        setUser(res.data.user);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });

    // 2. Establish Live WebSockets Session Broker
    const wsScheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Fallback URL config for development servers
    const wsHost = window.location.host;
    const wsUrl = `${wsScheme}//${wsHost}/api/ws`;
    
    let socket: WebSocket;
    const connectWS = () => {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "log") {
            setLogs((prev) => [...prev.slice(-199), data]); // Cap screen memory logs size to 200 items
          }
        } catch (err) {
          // ignore parsing error
        }
      };

      socket.onclose = () => {
        // Retry connection after 5 seconds
        setTimeout(connectWS, 5000);
      };
    };

    connectWS();
    return () => {
      if (socket) socket.close();
    };
  }, []);

  const clearLogs = () => {
    setLogs([]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex justify-center items-center">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const ProtectedRoute = ({ children }: { children: React.ReactElement }) => {
    return user ? children : <Navigate to="/" replace />;
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/guilds" replace /> : <Landing />} />
        
        <Route
          path="/guilds"
          element={
            <ProtectedRoute>
              <GuildSelect />
            </ProtectedRoute>
          }
        />

        <Route
          path="/guilds/:guildId"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="" element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="settings" element={<Settings />} />
          <Route path="music" element={<Music />} />
          <Route path="moderation" element={<Moderation />} />
          <Route path="tickets" element={<Tickets />} />
          <Route path="welcome" element={<Welcome />} />
          <Route path="ai" element={<AIConfigPage />} />
          <Route path="logs" element={<Logs logs={logs} clearLogs={clearLogs} />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
