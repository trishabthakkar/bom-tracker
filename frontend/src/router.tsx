import { createBrowserRouter } from "react-router-dom";
import { App } from "@/App";
import { DependencyGraphPage } from "@/pages/DependencyGraphPage";
import { HistoryPage } from "@/pages/HistoryPage";
import { HomePage } from "@/pages/HomePage";
import { ReportsPage } from "@/pages/ReportsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { UploadBomPage } from "@/pages/UploadBomPage";
import { UploadEcoPage } from "@/pages/UploadEcoPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "upload-bom", element: <UploadBomPage /> },
      { path: "upload-eco", element: <UploadEcoPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "dependency-graph", element: <DependencyGraphPage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);
