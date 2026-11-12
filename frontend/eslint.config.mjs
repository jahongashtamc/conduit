import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const eslintConfig = [
  {
    ignores: ["node_modules/**", ".next/**", "out/**", "next-env.d.ts"],
  },
  ...nextCoreWebVitals,
  ...nextTypescript,
  {
    rules: {
      // MVP: mavjud kod bazasida ogohlik darajasida — xatolar to'sqinlik qilmaydi
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      // Mount-da fetch qilib state o'rnatish patterni hozircha warn —
      // to'g'ri refaktor (event-driven/SWR) keyingi iteratsiya rejasi.
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];

export default eslintConfig;
