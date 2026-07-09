import { createBrowserRouter } from "react-router-dom";
import { App } from "@/App";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { PublicRoute } from "@/auth/PublicRoute";
import { BomComparePage } from "@/pages/BomComparePage";
import { DependencyGraphPage } from "@/pages/DependencyGraphPage";
import { DocumentsPage } from "@/pages/DocumentsPage";
import { HistoryPage } from "@/pages/HistoryPage";
import { HomePage } from "@/pages/HomePage";
import { AuthLayout } from "@/pages/AuthLayout";
import { LoginPage } from "@/pages/LoginPage";
import { ReportDetailPage } from "@/pages/ReportDetailPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { UploadBomPage } from "@/pages/UploadBomPage";
import { UploadEcoPage } from "@/pages/UploadEcoPage";

export const router = createBrowserRouter([
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/register", element: <RegisterPage /> },
        ],
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/",
        element: <App />,
        children: [
          { index: true, element: <HomePage /> },
          { path: "upload-bom", element: <UploadBomPage /> },
          { path: "bom-compare", element: <BomComparePage /> },
          { path: "upload-eco", element: <UploadEcoPage /> },
          { path: "documents", element: <DocumentsPage /> },
          { path: "reports", element: <ReportsPage /> },
          { path: "reports/:reportId", element: <ReportDetailPage /> },
          { path: "dependency-graph", element: <DependencyGraphPage /> },
          { path: "history", element: <HistoryPage /> },
          { path: "settings", element: <SettingsPage /> },
        ],
      },
    ],
  },
]);
