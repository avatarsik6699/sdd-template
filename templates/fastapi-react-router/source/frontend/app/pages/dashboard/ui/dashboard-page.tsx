import { useTranslation } from "react-i18next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DashboardPage() {
  const { t } = useTranslation("common");

  return (
    <main className="shell">
      <Card className="card">
        <CardHeader>
          <p className="eyebrow">{t("dashboardLabel")}</p>
          <CardTitle>{t("brand")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="lede">{t("dashboardDescription")}</p>
        </CardContent>
      </Card>
    </main>
  );
}
