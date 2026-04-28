import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AdminSessionProvider } from "./context/AdminSessionContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AdminSessionProvider>
      <App />
    </AdminSessionProvider>
  </React.StrictMode>,
);
