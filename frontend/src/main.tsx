import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { router } from "@/app/router";
import { AppSessionProvider } from "@/features/auth/session/AppSessionProvider";
import "@/styles/global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppSessionProvider>
      <RouterProvider router={router} />
    </AppSessionProvider>
  </React.StrictMode>,
);
