import { HomePage } from "@pages/home/ui/home-page";

export function meta() {
  return [
    { title: "[PROJECT_NAME]" },
    {
      name: "description",
      content: "[PROJECT_NAME] built on FastAPI and React Router SSR.",
    },
    {
      tagName: "link",
      rel: "canonical",
      href: "https://example.com/",
    },
  ];
}

export default function HomeRoute() {
  return <HomePage />;
}
