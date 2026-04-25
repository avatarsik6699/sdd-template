import { api } from "@shared/api/client";
import { LanguageSwitcher } from "@shared/ui/language-switcher";
import { ThemeToggle } from "@shared/ui/theme-toggle";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export async function loader() {
  const { data, error } = await api.get("/api/v1/auth/me");
  if (error) throw new Response("Unauthorized", { status: 401 });
  return data; // typed from the generated schema
}

export function HomePage() {
  const { t } = useTranslation("common");

  return (
    <main className="shell">
      <Card className="hero">
        <CardHeader>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="eyebrow">{t("stackLabel")}</p>
            <div className="flex flex-wrap items-center gap-3">
              <LanguageSwitcher />
              <ThemeToggle />
            </div>
          </div>
          <CardTitle className="text-4xl">{t("homeTitle")}</CardTitle>
          <CardDescription className="lede">{t("homeDescription")}</CardDescription>
        </CardHeader>
        <CardContent />
        <CardFooter>
          <Button asChild>
            <a href="/login">{t("openLoginRoute")}</a>
          </Button>
        </CardFooter>
      </Card>
    </main>
  );
}
