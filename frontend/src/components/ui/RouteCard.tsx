import type { ReactNode } from "react";

type RouteCardProps = {
  title: string;
  description: string;
  icon: ReactNode;
};

export function RouteCard({ title, description, icon }: RouteCardProps) {
  return (
    <article className="route-card">
      <div className="route-card__icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}
