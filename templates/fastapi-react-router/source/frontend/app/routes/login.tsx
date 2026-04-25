import { LoginPage } from "@pages/login/ui/login-page";

export function meta() {
  return [
    { title: "[PROJECT_NAME] Login" },
    {
      name: "description",
      content: "Authentication entry route for [PROJECT_NAME].",
    },
  ];
}

export default function LoginRoute() {
  return <LoginPage />;
}
