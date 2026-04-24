import { renderToStaticMarkup } from "react-dom/server";

import HomeRoute, { meta } from "../app/routes/home";

describe("home route", () => {
  it("renders the project placeholder headline", () => {
    const markup = renderToStaticMarkup(<HomeRoute />);

    expect(markup).toContain("[PROJECT_NAME]");
    expect(meta()[0]).toEqual({ title: "[PROJECT_NAME]" });
  });
});
