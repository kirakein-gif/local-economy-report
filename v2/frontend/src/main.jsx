import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./final.css";
import "./streamlit-theme.css";
import "./workflow-rich.css";

// UI bundle marker: rich-workflow-v1. The final commit intentionally redeploys
// the complete JSX + theme + workflow CSS together after the staged UI updates.
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
