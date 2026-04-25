import { DashboardPage } from "@pages/dashboard/ui/dashboard-page";

export function meta() {
  return [
    { title: "[PROJECT_NAME] Dashboard" },
    {
      name: "description",
      content: "Protected dashboard placeholder for [PROJECT_NAME].",
    },
  ];
}

export default function DashboardRoute() {
  return <DashboardPage />;
}
