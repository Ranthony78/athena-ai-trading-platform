/* ESLint config. Formatting is Prettier's job (see .prettierrc.json), so
   eslint-config-prettier comes last to switch off any conflicting rules. */
module.exports = {
    root: true,
    env: { browser: true, es2022: true },
    extends: [
        "eslint:recommended",
        "plugin:react/recommended",
        "plugin:react/jsx-runtime",
        "plugin:react-hooks/recommended",
        "prettier",
    ],
    parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
    },
    settings: { react: { version: "detect" } },
    ignorePatterns: ["dist", "node_modules"],
    rules: {
        // The code base does not use PropTypes.
        "react/prop-types": "off",
        // A leading underscore marks an intentionally unused name.
        "no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
    },
    overrides: [
        {
            // Tooling config files run in Node, not the browser.
            files: ["*.config.js", "*.cjs"],
            env: { node: true },
        },
    ],
};
