import { I18nextProvider } from "react-i18next";
import { renderToStaticMarkup } from "react-dom/server";

import { i18n } from "../app/shared/lib/i18n";
import HomeRoute, { meta } from "../app/routes/home";

describe("home route", () => {
  it("renders the [PROJECT_NAME] headline", () => {
    const markup = renderToStaticMarkup(
      <I18nextProvider i18n={i18n}>
        <HomeRoute />
      </I18nextProvider>,
    );

    expect(markup).toContain("[PROJECT_NAME]");
    expect(meta()[0]).toEqual({ title: "[PROJECT_NAME]" });
  });
});
