import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginPage() {
  const { t } = useTranslation("common");

  return (
    <main className="shell shell-narrow">
      <Card className="card">
        <CardHeader>
          <p className="eyebrow">{t("loginLabel")}</p>
          <CardTitle>{t("brand")}</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="form">
            <div className="grid gap-1.5">
              <Label htmlFor="email">{t("email")}</Label>
              <Input id="email" name="email" type="email" autoComplete="email" />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="password">{t("password")}</Label>
              <Input id="password" name="password" type="password" autoComplete="current-password" />
            </div>
            <Button type="submit" className="w-fit">
              {t("continue")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
