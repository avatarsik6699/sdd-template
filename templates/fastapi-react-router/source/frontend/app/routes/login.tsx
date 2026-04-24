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
  return (
    <main className="shell shell-narrow">
      <section className="card">
        <p className="eyebrow">Login</p>
        <h1>[PROJECT_NAME]</h1>
        <form className="form">
          <label>
            Email
            <input name="email" type="email" autoComplete="email" />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete="current-password" />
          </label>
          <button type="submit">Continue</button>
        </form>
      </section>
    </main>
  );
}
