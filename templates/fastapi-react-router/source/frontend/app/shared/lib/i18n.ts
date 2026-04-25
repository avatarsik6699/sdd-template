import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    common: {
      brand: "[PROJECT_NAME]",
      stackLabel: "SSR Reference Stack",
      homeTitle: "[PROJECT_NAME]",
      homeDescription:
        "FastAPI handles the API surface. React Router handles SSR, routing, and SEO metadata.",
      openLoginRoute: "Open login route",
      dashboardLabel: "Dashboard",
      dashboardDescription:
        "This route is the placeholder for authenticated application work in the React Router stack.",
      loginLabel: "Login",
      email: "Email",
      password: "Password",
      continue: "Continue",
      language: "Language",
      theme: "Theme",
      light: "Light",
      dark: "Dark",
      system: "System",
    },
  },
  ru: {
    common: {
      brand: "[PROJECT_NAME]",
      stackLabel: "SSR опорный стек",
      homeTitle: "[PROJECT_NAME]",
      homeDescription:
        "FastAPI отвечает за API. React Router отвечает за SSR, маршрутизацию и SEO-метаданные.",
      openLoginRoute: "Открыть страницу входа",
      dashboardLabel: "Панель",
      dashboardDescription:
        "Эта страница — заглушка для авторизованной части приложения на стеке React Router.",
      loginLabel: "Вход",
      email: "Email",
      password: "Пароль",
      continue: "Продолжить",
      language: "Язык",
      theme: "Тема",
      light: "Светлая",
      dark: "Темная",
      system: "Системная",
    },
  },
} as const;

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    supportedLngs: ["en", "ru"],
    defaultNS: "common",
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
    },
  });

export { i18n };
