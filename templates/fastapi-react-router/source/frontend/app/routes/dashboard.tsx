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
  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">Dashboard</p>
        <h1>[PROJECT_NAME]</h1>
        <p className="lede">
          This route is the placeholder for authenticated application work in the React Router
          stack.
        </p>
      </section>
    </main>
  );
}
