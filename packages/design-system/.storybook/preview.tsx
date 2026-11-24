import * as React from "react";
import type { Preview } from "@storybook/react";
import "../src/styles/fonts.css";
import "../src/styles/tokens.css";
import "./storybook.css";

const preview: Preview = {
  parameters: { layout: "centered", backgrounds: { disable: true }, a11y: { test: "error" } },
  globalTypes: {
    theme: {
      description: "Theme",
      toolbar: { title: "Theme", icon: "circlehollow", items: ["dark", "light"], dynamicTitle: true },
    },
  },
  initialGlobals: { theme: "dark" },
  decorators: [
    (Story, ctx) => {
      document.documentElement.dataset.theme = ctx.globals.theme === "light" ? "light" : "dark";
      return (
        <div className="bg-bg p-8 font-sans text-fg">
          <Story />
        </div>
      );
    },
  ],
};
export default preview;
