import { useTheme } from "next-themes";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";

const themes = ["light", "dark", "system"] as const;

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const { t } = useTranslation("common");

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">{t("theme")}</span>
      <div className="inline-flex rounded-lg border border-border bg-background p-1">
        {themes.map((value) => (
          <Button
            key={value}
            type="button"
            size="xs"
            variant={theme === value ? "default" : "ghost"}
            onClick={() => setTheme(value)}
            className="capitalize"
          >
            {t(value)}
          </Button>
        ))}
      </div>
    </div>
  );
}
