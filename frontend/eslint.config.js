// ESLint flat config (ESLint 9+; replaces the old .eslintrc.cjs).
// Formatting is Prettier's job (see .prettierrc.json), so eslint-config-prettier
// comes last to switch off any rule that would fight the formatter.
import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";

export default [
    { ignores: ["dist", "node_modules", "public"] },

    js.configs.recommended,
    react.configs.flat.recommended,
    react.configs.flat["jsx-runtime"],

    {
        files: ["**/*.{js,jsx}"],
        plugins: { "react-hooks": reactHooks },
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "module",
            globals: { ...globals.browser },
            parserOptions: { ecmaFeatures: { jsx: true } },
        },
        settings: { react: { version: "detect" } },
        rules: {
            // Only the two classic hook rules. The plugin's newer "recommended"
            // preset adds many React Compiler rules that would tighten the
            // code base, not just migrate the tooling.
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
            // The code base does not use PropTypes.
            "react/prop-types": "off",
            // A leading underscore marks an intentionally unused name.
            "no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
        },
    },

    {
        // Tooling config files run in Node, not the browser.
        files: ["*.config.js"],
        languageOptions: { globals: { ...globals.node } },
    },

    prettier,
];
