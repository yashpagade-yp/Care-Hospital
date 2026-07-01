import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type ButtonLinkProps = {
  to: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
};

export function ButtonLink({
  to,
  children,
  variant = "primary",
}: ButtonLinkProps) {
  return (
    <Link to={to} className={`button ${variant === "secondary" ? "button--secondary" : "button--primary"}`}>
      {children}
    </Link>
  );
}
